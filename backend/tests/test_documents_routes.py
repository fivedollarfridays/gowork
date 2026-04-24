"""Tests for the documents API router (T12.17).

Seven endpoints under ``/api/documents``:

- POST /api/documents/resume                    — generate via T12.15
- GET  /api/documents/resume/{version_id}        — markdown
- GET  /api/documents/resume/{version_id}/pdf    — PDF
- POST /api/documents/cover-letter               — generate via T12.16
- GET  /api/documents/cover-letter/{version_id}  — markdown
- GET  /api/documents/cover-letter/{version_id}/pdf  — PDF
- GET  /api/documents/versions                   — newest-first list

Auth contract mirrors T12.10 / T12.13: ``token`` query param against
``feedback_tokens``; cross-session access returns 403.

PDF assertions check the ``%PDF-`` magic bytes (not just non-empty)
to confirm WeasyPrint actually rendered output.

Use-counter hook (T12.17): ``POST /api/job-applications`` with a
``resume_version_id`` must increment the corresponding
``resume_versions.use_counter`` row exactly once.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core import events
from app.core.migrations import runner

_SESSION_A = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
_SESSION_B = "bbbbbbbb-cccc-dddd-eeee-ffffffffffff"
_TOKEN_A = "tok-aaaaa-docs"
_TOKEN_B = "tok-bbbbb-docs"


# -------------------- Fixtures --------------------


@pytest.fixture(autouse=True)
def _isolate_event_bus() -> Iterator[None]:
    events.clear_all_subscribers()
    yield
    events.clear_all_subscribers()


@pytest.fixture
def db_path(tmp_path: Path) -> str:
    path = str(tmp_path / "documents_api.db")
    runner.apply_pending(path)
    _seed_session(path, _SESSION_A, _TOKEN_A)
    _seed_session(path, _SESSION_B, _TOKEN_B)
    return path


def _seed_session(path: str, session_id: str, token: str) -> None:
    conn = sqlite3.connect(path)
    try:
        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()
        expires_iso = (now + timedelta(days=30)).isoformat()
        profile_json = (
            '{"name": "Worker Sample", "summary": "Reliable.", '
            '"work_history": [{"title": "Cook", "description": "kitchen"}]}'
        )
        conn.execute(
            "INSERT INTO sessions (id, profile, created_at, "
            "barriers, expires_at) VALUES (?, ?, ?, ?, ?)",
            (session_id, profile_json, now_iso, "[]", expires_iso),
        )
        conn.execute(
            "INSERT INTO feedback_tokens "
            "(token, session_id, created_at, expires_at) "
            "VALUES (?, ?, ?, ?)",
            (token, session_id, now_iso, expires_iso),
        )
        conn.commit()
    finally:
        conn.close()


@pytest.fixture
def client(db_path: str, monkeypatch) -> TestClient:
    from app.routes import documents as documents_route

    monkeypatch.setattr(
        documents_route, "_resolve_db_path", lambda: db_path,
    )
    app = FastAPI()
    app.include_router(documents_route.router)
    return TestClient(app)


@pytest.fixture
def jobs_app_client(db_path: str, monkeypatch) -> TestClient:
    """A second TestClient mounting the jobs-applications router.

    Used to verify the T12.17 use-counter hook fires when a job
    application is created with a ``resume_version_id``.
    """
    from app.routes import jobs_applications as jobs_route

    monkeypatch.setattr(
        jobs_route, "_resolve_db_path", lambda: db_path,
    )
    app = FastAPI()
    app.include_router(jobs_route.router)
    return TestClient(app)


# -------------------- POST /api/documents/resume --------------------


def test_post_resume_returns_version_payload(client: TestClient) -> None:
    """POST /resume should generate and persist a version row."""
    resp = client.post(
        f"/api/documents/resume?token={_TOKEN_A}",
        json={"session_id": _SESSION_A},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["session_id"] == _SESSION_A
    assert body["doc_type"] == "resume"
    assert isinstance(body["version_id"], int) and body["version_id"] > 0
    assert body["version_counter"] == 1
    assert body["generation_method"] in {"template", "llm"}


def test_post_resume_rejects_token_session_mismatch(
    client: TestClient,
) -> None:
    resp = client.post(
        f"/api/documents/resume?token={_TOKEN_A}",
        json={"session_id": _SESSION_B},
    )
    assert resp.status_code == 403


# -------------------- GET /api/documents/resume/{id} --------------------


def test_get_resume_returns_markdown_content_type(
    client: TestClient,
) -> None:
    create = client.post(
        f"/api/documents/resume?token={_TOKEN_A}",
        json={"session_id": _SESSION_A},
    )
    version_id = create.json()["version_id"]
    resp = client.get(
        f"/api/documents/resume/{version_id}?token={_TOKEN_A}",
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/markdown")
    assert resp.text  # non-empty


def test_get_resume_404_when_missing(client: TestClient) -> None:
    resp = client.get(
        f"/api/documents/resume/999999?token={_TOKEN_A}",
    )
    assert resp.status_code == 404


def test_get_resume_403_cross_session(client: TestClient) -> None:
    create = client.post(
        f"/api/documents/resume?token={_TOKEN_A}",
        json={"session_id": _SESSION_A},
    )
    version_id = create.json()["version_id"]
    resp = client.get(
        f"/api/documents/resume/{version_id}?token={_TOKEN_B}",
    )
    assert resp.status_code == 403


# -------------------- GET /api/documents/resume/{id}/pdf --------------------


def test_get_resume_pdf_returns_pdf_bytes(client: TestClient) -> None:
    create = client.post(
        f"/api/documents/resume?token={_TOKEN_A}",
        json={"session_id": _SESSION_A},
    )
    version_id = create.json()["version_id"]
    resp = client.get(
        f"/api/documents/resume/{version_id}/pdf?token={_TOKEN_A}",
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/pdf")
    # %PDF- is the mandatory magic header byte sequence.
    assert resp.content.startswith(b"%PDF-"), (
        "Response did not start with PDF magic bytes"
    )


def test_get_resume_pdf_403_cross_session(client: TestClient) -> None:
    create = client.post(
        f"/api/documents/resume?token={_TOKEN_A}",
        json={"session_id": _SESSION_A},
    )
    version_id = create.json()["version_id"]
    resp = client.get(
        f"/api/documents/resume/{version_id}/pdf?token={_TOKEN_B}",
    )
    assert resp.status_code == 403


def test_pdf_render_failure_returns_generic_detail(
    client: TestClient, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """S5: PdfRenderError must NOT leak its exception text to the caller.

    The previous implementation interpolated the raw exception
    (filesystem paths, CSS internals) into the 500 detail. The fix
    returns a generic ``"PDF rendering failed"`` and routes the full
    exception to ``logger.exception`` for operator-side diagnosis.
    """
    from app.core import pdf_renderer
    from app.routes import documents as docs_route

    create = client.post(
        f"/api/documents/resume?token={_TOKEN_A}",
        json={"session_id": _SESSION_A},
    )
    version_id = create.json()["version_id"]

    sensitive = "/var/lib/secrets/key.pem missing — leaked path"

    def _boom(*args, **kwargs):
        raise pdf_renderer.PdfRenderError(sensitive)

    monkeypatch.setattr(docs_route, "render_markdown_to_pdf", _boom)

    resp = client.get(
        f"/api/documents/resume/{version_id}/pdf?token={_TOKEN_A}",
    )
    assert resp.status_code == 500
    body = resp.json()
    assert body["detail"] == "PDF rendering failed", body
    assert sensitive not in resp.text, (
        f"sensitive exception text leaked to caller: {resp.text!r}"
    )


# -------------------- POST /api/documents/cover-letter --------------------


def test_post_cover_letter_creates_version(client: TestClient) -> None:
    resume_resp = client.post(
        f"/api/documents/resume?token={_TOKEN_A}",
        json={"session_id": _SESSION_A},
    )
    resume_id = resume_resp.json()["version_id"]
    resp = client.post(
        f"/api/documents/cover-letter?token={_TOKEN_A}",
        json={
            "session_id": _SESSION_A,
            "resume_version_id": resume_id,
            "job_match_ref": {
                "employer": "Local Cafe",
                "city_slug": "montgomery",
            },
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["session_id"] == _SESSION_A
    assert body["doc_type"] == "cover_letter"
    assert isinstance(body["version_id"], int) and body["version_id"] > 0
    assert "fair_chance" in body


def test_post_cover_letter_rejects_session_mismatch(
    client: TestClient,
) -> None:
    resp = client.post(
        f"/api/documents/cover-letter?token={_TOKEN_A}",
        json={
            "session_id": _SESSION_B,
            "resume_version_id": 1,
            "job_match_ref": {"employer": "X", "city_slug": "montgomery"},
        },
    )
    assert resp.status_code == 403


# -------------------- GET /api/documents/cover-letter/{id} --------------------


def test_get_cover_letter_markdown(client: TestClient) -> None:
    resume_id = client.post(
        f"/api/documents/resume?token={_TOKEN_A}",
        json={"session_id": _SESSION_A},
    ).json()["version_id"]
    cl_id = client.post(
        f"/api/documents/cover-letter?token={_TOKEN_A}",
        json={
            "session_id": _SESSION_A,
            "resume_version_id": resume_id,
            "job_match_ref": {
                "employer": "Local Cafe",
                "city_slug": "montgomery",
            },
        },
    ).json()["version_id"]
    resp = client.get(
        f"/api/documents/cover-letter/{cl_id}?token={_TOKEN_A}",
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/markdown")
    assert resp.text


def test_get_cover_letter_pdf_starts_with_magic(client: TestClient) -> None:
    resume_id = client.post(
        f"/api/documents/resume?token={_TOKEN_A}",
        json={"session_id": _SESSION_A},
    ).json()["version_id"]
    cl_id = client.post(
        f"/api/documents/cover-letter?token={_TOKEN_A}",
        json={
            "session_id": _SESSION_A,
            "resume_version_id": resume_id,
            "job_match_ref": {
                "employer": "Local Cafe",
                "city_slug": "montgomery",
            },
        },
    ).json()["version_id"]
    resp = client.get(
        f"/api/documents/cover-letter/{cl_id}/pdf?token={_TOKEN_A}",
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/pdf")
    assert resp.content.startswith(b"%PDF-")


def test_get_cover_letter_pdf_404(client: TestClient) -> None:
    resp = client.get(
        f"/api/documents/cover-letter/999999/pdf?token={_TOKEN_A}",
    )
    assert resp.status_code == 404


# -------------------- GET /api/documents/versions --------------------


def test_versions_list_newest_first_and_session_scoped(
    client: TestClient, db_path: str,
) -> None:
    """Versions list should be newest-first and exclude other sessions."""
    # Create two resume versions for session A.
    first_id = client.post(
        f"/api/documents/resume?token={_TOKEN_A}",
        json={"session_id": _SESSION_A},
    ).json()["version_id"]
    second_id = client.post(
        f"/api/documents/resume?token={_TOKEN_A}",
        json={"session_id": _SESSION_A},
    ).json()["version_id"]
    # And one for session B that must not leak.
    client.post(
        f"/api/documents/resume?token={_TOKEN_B}",
        json={"session_id": _SESSION_B},
    )

    resp = client.get(
        f"/api/documents/versions?session_id={_SESSION_A}&token={_TOKEN_A}",
    )
    assert resp.status_code == 200
    rows = resp.json()
    ids = [r["version_id"] for r in rows]
    assert ids == [second_id, first_id]
    # All belong to session A only.
    assert all(r["session_id"] == _SESSION_A for r in rows)


def test_versions_list_403_cross_session(client: TestClient) -> None:
    resp = client.get(
        f"/api/documents/versions?session_id={_SESSION_B}&token={_TOKEN_A}",
    )
    assert resp.status_code == 403


# -------------------- T12.17 hook: use_counter --------------------


def test_application_create_increments_use_counter(
    client: TestClient,
    jobs_app_client: TestClient,
    db_path: str,
) -> None:
    """POST /api/job-applications must bump resume_versions.use_counter."""
    create = client.post(
        f"/api/documents/resume?token={_TOKEN_A}",
        json={"session_id": _SESSION_A},
    )
    version_id = create.json()["version_id"]

    # Pre-condition: counter starts at zero.
    assert _read_use_counter(db_path, version_id) == 0

    resp = jobs_app_client.post(
        f"/api/job-applications?token={_TOKEN_A}",
        json={
            "session_id": _SESSION_A,
            "match_source": "indeed",
            "match_url": "https://example.com/job/123",
            "company": "Local Cafe",
            "role": "Cook",
            "resume_version_id": version_id,
        },
    )
    assert resp.status_code == 201, resp.text
    assert _read_use_counter(db_path, version_id) == 1


def test_application_create_without_version_id_no_increment(
    jobs_app_client: TestClient, db_path: str,
) -> None:
    """No resume_version_id → no use_counter side-effect anywhere."""
    resp = jobs_app_client.post(
        f"/api/job-applications?token={_TOKEN_A}",
        json={
            "session_id": _SESSION_A,
            "match_source": "indeed",
            "match_url": "https://example.com/job/456",
            "company": "Diner",
            "role": "Server",
        },
    )
    assert resp.status_code == 201


def _read_use_counter(db_path: str, version_id: int) -> int:
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute(
            "SELECT use_counter FROM resume_versions WHERE id = ?",
            (version_id,),
        ).fetchone()
    finally:
        conn.close()
    return int(row[0]) if row else 0


# -------------------- Router registration --------------------


def test_documents_router_registered_in_all_routers() -> None:
    """The documents router must be present in routes.all_routers."""
    from app.routes import all_routers
    from app.routes.documents import router as documents_router

    assert documents_router in all_routers

"""Per-session rate limiting on LLM-invoking documents endpoints (T13.99).

The two POST endpoints in :mod:`app.routes.documents` invoke the LLM
when ``ENABLE_AI_GENERATION=true``:

* ``POST /api/documents/resume``       — resume_builder.generate_resume
* ``POST /api/documents/cover-letter`` — cover_letter_builder.generate_cover_letter

Without a per-session rate limit, a single session could trigger many
expensive LLM calls per minute. The audit (T13.99 HIGH) flags this as
a cost + abuse risk.

These tests mirror the pattern in :mod:`tests.test_rate_limit`'s
``TestPlanGenerateRateLimit`` class:

1. Reset the limiter at start of each test (per-test isolation).
2. Hit the endpoint ``max_requests`` times and assert success codes.
3. Hit it once more and assert ``429``.
4. Per-key isolation: a second session is unaffected by the first
   session's saturation. This pins the "per-session" axis — if a
   future refactor accidentally key-by-IP, both sessions would share
   one IP under TestClient and the second session's request would
   spuriously 429.
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

_SESSION_A = "11111111-2222-3333-4444-555555555555"
_SESSION_B = "66666666-7777-8888-9999-aaaaaaaaaaaa"
_TOKEN_A = "tok-rate-aaaa"
_TOKEN_B = "tok-rate-bbbb"


# -------------------- Fixtures --------------------


@pytest.fixture(autouse=True)
def _isolate_event_bus() -> Iterator[None]:
    events.clear_all_subscribers()
    yield
    events.clear_all_subscribers()


@pytest.fixture(autouse=True)
def _reset_doc_rate_limiter() -> Iterator[None]:
    """Each test starts with a clean limiter so order does not matter."""
    from app.routes.documents import _doc_gen_rate_limiter

    _doc_gen_rate_limiter.clear()
    yield
    _doc_gen_rate_limiter.clear()


@pytest.fixture
def db_path(tmp_path: Path) -> str:
    path = str(tmp_path / "documents_rate_limit.db")
    runner.apply_pending(path)
    _seed_session(path, _SESSION_A, _TOKEN_A)
    _seed_session(path, _SESSION_B, _TOKEN_B)
    return path


def _seed_session(path: str, session_id: str, token: str) -> None:
    """Insert a sessions row + matching feedback_tokens row.

    Mirrors ``_seed_session`` in ``test_documents_routes.py`` so the
    LLM-builder stub finds a profile to read.
    """
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


# -------------------- POST /resume --------------------


def test_resume_create_rate_limited(client: TestClient) -> None:
    """Sixth resume POST in the same window must return 429.

    Five rapid resume creations for one session should all succeed,
    then the sixth must be rejected with 429.
    """
    url = f"/api/documents/resume?token={_TOKEN_A}"
    body = {"session_id": _SESSION_A}
    for _ in range(5):
        resp = client.post(url, json=body)
        assert resp.status_code == 201, resp.text
    resp = client.post(url, json=body)
    assert resp.status_code == 429, resp.text
    assert "rate" in resp.json()["detail"].lower() or "many" in resp.json()["detail"].lower()


def test_resume_rate_limit_is_per_session(client: TestClient) -> None:
    """A second session is NOT throttled when session A is saturated.

    This pins the per-session keying. Under TestClient, both sessions
    share the same client IP (``testclient``); if a regression keys by
    IP, this test would fail because session B would inherit A's quota.
    """
    saturate_url = f"/api/documents/resume?token={_TOKEN_A}"
    saturate_body = {"session_id": _SESSION_A}
    for _ in range(5):
        client.post(saturate_url, json=saturate_body)
    # A is now saturated.
    over = client.post(saturate_url, json=saturate_body)
    assert over.status_code == 429

    # B should still have its full quota.
    b_resp = client.post(
        f"/api/documents/resume?token={_TOKEN_B}",
        json={"session_id": _SESSION_B},
    )
    assert b_resp.status_code == 201, b_resp.text


# -------------------- POST /cover-letter --------------------


def test_cover_letter_create_rate_limited(client: TestClient) -> None:
    """Sixth cover-letter POST in the same window must return 429.

    Cover-letter creation requires a resume version first, so the
    initial resume create consumes one limiter slot for session A.
    The five subsequent cover-letter creates exhaust the remaining
    quota; the seventh request (resume + 6 cover-letters = 7) hits
    429 because the shared per-session quota is already at 6.

    To keep the assertion crisp we seed a resume first (consuming
    one slot), then issue 4 cover-letter creates (5 total), and
    confirm the 6th total request — the 5th cover-letter — is denied.
    """
    resume_resp = client.post(
        f"/api/documents/resume?token={_TOKEN_A}",
        json={"session_id": _SESSION_A},
    )
    assert resume_resp.status_code == 201, resume_resp.text
    resume_id = resume_resp.json()["version_id"]

    cl_url = f"/api/documents/cover-letter?token={_TOKEN_A}"
    cl_body = {
        "session_id": _SESSION_A,
        "resume_version_id": resume_id,
        "job_match_ref": {
            "employer": "Local Cafe", "city_slug": "montgomery",
        },
    }

    # We've used 1 slot for the resume above. Four more creates fit.
    for _ in range(4):
        resp = client.post(cl_url, json=cl_body)
        assert resp.status_code == 201, resp.text

    # Sixth total request (5th cover-letter) must be rate limited.
    resp = client.post(cl_url, json=cl_body)
    assert resp.status_code == 429, resp.text

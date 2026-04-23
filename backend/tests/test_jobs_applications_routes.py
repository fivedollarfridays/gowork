"""Tests for the job-applications API router (T12.13).

Five endpoints under ``/api/job-applications`` (hyphenated — distinct from
the existing ``/api/jobs/{job_id}`` resource in ``routes/jobs.py``):

- GET    /api/job-applications?session_id=X
- POST   /api/job-applications
- PATCH  /api/job-applications/{id}
- GET    /api/job-applications/funnel?session_id=X
- GET    /api/job-applications/community-funnel?segment_by=X

Auth: same shape as T12.10 appointments — ``token`` query param against
``feedback_tokens``; session-owned endpoints additionally enforce that
``token.session_id`` matches the target row's session.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core import events
from app.core.migrations import runner
from app.routes import jobs_applications as jobs_applications_route

_SESSION_A = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
_SESSION_B = "bbbbbbbb-cccc-dddd-eeee-ffffffffffff"
_TOKEN_A = "tok-aaaaa"
_TOKEN_B = "tok-bbbbb"
_CITY_A = "montgomery"
_CITY_B = "fort-worth"


# -------------------- Fixtures --------------------


@pytest.fixture(autouse=True)
def _isolate_event_bus():
    events.clear_all_subscribers()
    yield
    events.clear_all_subscribers()


@pytest.fixture
def db_path(tmp_path: Path) -> str:
    path = str(tmp_path / "jobs_api.db")
    runner.apply_pending(path)
    _seed_session(path, _SESSION_A, _TOKEN_A, city=_CITY_A)
    _seed_session(path, _SESSION_B, _TOKEN_B, city=_CITY_B)
    return path


def _seed_session(
    path: str, session_id: str, token: str, *, city: str,
) -> None:
    """Insert a session + feedback_token + outcomes_records tag for city scope."""
    conn = sqlite3.connect(path)
    try:
        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()
        expires_iso = (now + timedelta(days=30)).isoformat()
        conn.execute(
            "INSERT INTO sessions (id, created_at, barriers, expires_at) "
            "VALUES (?, ?, ?, ?)",
            (session_id, now_iso, "[]", expires_iso),
        )
        conn.execute(
            "INSERT INTO feedback_tokens "
            "(token, session_id, created_at, expires_at) "
            "VALUES (?, ?, ?, ?)",
            (token, session_id, now_iso, expires_iso),
        )
        conn.execute(
            "INSERT INTO outcomes_records "
            "(session_id, event_type, payload_json, created_at, "
            "barriers_cleared_snapshot_json) VALUES (?, ?, ?, ?, ?)",
            (
                session_id, "session_tagged",
                json.dumps({"city": city}), now_iso, "[]",
            ),
        )
        conn.commit()
    finally:
        conn.close()


def _seed_extra_session(
    path: str, session_id: str, *, city: str,
) -> None:
    """Seed a session in a given city without a token (aggregates-only use)."""
    conn = sqlite3.connect(path)
    try:
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "INSERT INTO sessions (id, created_at, barriers, expires_at) "
            "VALUES (?, ?, ?, ?)",
            (session_id, now, "[]", now),
        )
        conn.execute(
            "INSERT INTO outcomes_records "
            "(session_id, event_type, payload_json, created_at, "
            "barriers_cleared_snapshot_json) VALUES (?, ?, ?, ?, ?)",
            (
                session_id, "session_tagged",
                json.dumps({"city": city}), now, "[]",
            ),
        )
        conn.commit()
    finally:
        conn.close()


def _seed_application(
    path: str, session_id: str, *, match_url_suffix: str = "",
    status: str = "draft",
) -> int:
    """Low-level insert that bypasses applications.create (for seeding bulk)."""
    from app.modules.jobs import applications
    from app.modules.common.temporal_types import JobApplicationStatus

    created = applications.create(
        session_id,
        match_source="indeed",
        match_url=f"https://indeed.com/job/{session_id}{match_url_suffix}",
        company="Acme",
        role="Tech",
        db_path=path,
    )
    if status != "draft":
        chain = {
            "applied": [JobApplicationStatus.APPLIED],
            "interview": [
                JobApplicationStatus.APPLIED, JobApplicationStatus.INTERVIEW,
            ],
            "offer": [
                JobApplicationStatus.APPLIED, JobApplicationStatus.INTERVIEW,
                JobApplicationStatus.OFFER,
            ],
            "rejected": [
                JobApplicationStatus.APPLIED, JobApplicationStatus.REJECTED,
            ],
        }[status]
        for nxt in chain:
            applications.update_status(created.id, nxt, db_path=path)
    return int(created.id)


@pytest.fixture
def client(db_path: str, monkeypatch) -> TestClient:
    monkeypatch.setattr(
        jobs_applications_route, "_resolve_db_path", lambda: db_path,
    )
    app = FastAPI()
    app.include_router(jobs_applications_route.router)
    return TestClient(app)


def _post_body(
    *,
    match_source: str | None = "indeed",
    match_url: str | None = "https://indeed.com/job/abc",
    company: str | None = "Acme",
    role: str | None = "Tech",
    resume_version_id: int | None = None,
    session_id: str = _SESSION_A,
) -> dict:
    return {
        "session_id": session_id,
        "match_source": match_source,
        "match_url": match_url,
        "company": company,
        "role": role,
        "resume_version_id": resume_version_id,
    }


# -------------------- GET /api/job-applications --------------------


def test_list_by_session_empty(client: TestClient) -> None:
    resp = client.get(
        f"/api/job-applications?session_id={_SESSION_A}&token={_TOKEN_A}",
    )
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_requires_valid_token(client: TestClient) -> None:
    resp = client.get(
        f"/api/job-applications?session_id={_SESSION_A}&token=bad",
    )
    assert resp.status_code == 401


def test_list_cross_session_token_returns_403(client: TestClient) -> None:
    resp = client.get(
        f"/api/job-applications?session_id={_SESSION_A}&token={_TOKEN_B}",
    )
    assert resp.status_code == 403


# -------------------- POST /api/job-applications --------------------


def test_post_creates_application(client: TestClient) -> None:
    resp = client.post(
        f"/api/job-applications?token={_TOKEN_A}",
        json=_post_body(),
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["id"] is not None
    assert body["session_id"] == _SESSION_A
    assert body["company"] == "Acme"
    assert body["status"] == "draft"
    assert body["match_source"] == "indeed"


def test_post_returns_created_in_list(client: TestClient) -> None:
    client.post(
        f"/api/job-applications?token={_TOKEN_A}",
        json=_post_body(),
    )
    resp = client.get(
        f"/api/job-applications?session_id={_SESSION_A}&token={_TOKEN_A}",
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_post_rejects_none_match_source(client: TestClient) -> None:
    """match_source must be non-null (composite-link invariant)."""
    resp = client.post(
        f"/api/job-applications?token={_TOKEN_A}",
        json=_post_body(match_source=None),
    )
    assert resp.status_code in (400, 422)


def test_post_rejects_empty_match_url(client: TestClient) -> None:
    resp = client.post(
        f"/api/job-applications?token={_TOKEN_A}",
        json=_post_body(match_url=""),
    )
    assert resp.status_code == 400


def test_post_mismatched_session_returns_403(client: TestClient) -> None:
    resp = client.post(
        f"/api/job-applications?token={_TOKEN_A}",
        json=_post_body(session_id=_SESSION_B),
    )
    assert resp.status_code == 403


def test_malformed_body_returns_422(client: TestClient) -> None:
    resp = client.post(
        f"/api/job-applications?token={_TOKEN_A}",
        json={"oops": True},  # missing session_id and everything
    )
    assert resp.status_code == 422


# -------------------- PATCH /api/job-applications/{id} --------------------


def test_patch_transitions_status(client: TestClient) -> None:
    created = client.post(
        f"/api/job-applications?token={_TOKEN_A}", json=_post_body(),
    ).json()
    resp = client.patch(
        f"/api/job-applications/{created['id']}?token={_TOKEN_A}",
        json={"status": "applied"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "applied"


def test_patch_invalid_transition_returns_409(client: TestClient) -> None:
    """rejected is terminal; rejected → applied is disallowed."""
    created = client.post(
        f"/api/job-applications?token={_TOKEN_A}", json=_post_body(),
    ).json()
    # Walk DRAFT → APPLIED → REJECTED
    client.patch(
        f"/api/job-applications/{created['id']}?token={_TOKEN_A}",
        json={"status": "applied"},
    )
    client.patch(
        f"/api/job-applications/{created['id']}?token={_TOKEN_A}",
        json={"status": "rejected"},
    )
    resp = client.patch(
        f"/api/job-applications/{created['id']}?token={_TOKEN_A}",
        json={"status": "applied"},
    )
    assert resp.status_code == 409


def test_patch_non_status_field_rejected(client: TestClient) -> None:
    """PATCH only mutates status; other fields → 400."""
    created = client.post(
        f"/api/job-applications?token={_TOKEN_A}", json=_post_body(),
    ).json()
    resp = client.patch(
        f"/api/job-applications/{created['id']}?token={_TOKEN_A}",
        json={"company": "OtherCo"},
    )
    assert resp.status_code == 400


def test_patch_missing_status_returns_400(client: TestClient) -> None:
    created = client.post(
        f"/api/job-applications?token={_TOKEN_A}", json=_post_body(),
    ).json()
    resp = client.patch(
        f"/api/job-applications/{created['id']}?token={_TOKEN_A}",
        json={},
    )
    assert resp.status_code == 400


def test_cross_session_patch_returns_403(client: TestClient) -> None:
    created = client.post(
        f"/api/job-applications?token={_TOKEN_A}", json=_post_body(),
    ).json()
    resp = client.patch(
        f"/api/job-applications/{created['id']}?token={_TOKEN_B}",
        json={"status": "applied"},
    )
    assert resp.status_code == 403


def test_patch_404_when_missing(client: TestClient) -> None:
    resp = client.patch(
        f"/api/job-applications/9999?token={_TOKEN_A}",
        json={"status": "applied"},
    )
    assert resp.status_code == 404


# -------------------- GET /funnel --------------------


def test_funnel_returns_structured_counts_and_rates(
    client: TestClient, db_path: str,
) -> None:
    _seed_application(db_path, _SESSION_A, match_url_suffix="-a", status="applied")
    _seed_application(db_path, _SESSION_A, match_url_suffix="-b", status="interview")
    resp = client.get(
        f"/api/job-applications/funnel"
        f"?session_id={_SESSION_A}&token={_TOKEN_A}",
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "counts" in body
    assert body["counts"]["applied"] == 1
    assert body["counts"]["interview"] == 1
    assert "draft_to_applied_rate" in body
    assert "applied_to_interview_rate" in body


def test_funnel_cross_session_returns_403(client: TestClient) -> None:
    resp = client.get(
        f"/api/job-applications/funnel"
        f"?session_id={_SESSION_A}&token={_TOKEN_B}",
    )
    assert resp.status_code == 403


# -------------------- GET /community-funnel --------------------


def test_community_funnel_returns_dict(
    client: TestClient, db_path: str,
) -> None:
    """≥5 sessions in session A's city → unsuppressed result dict."""
    _seed_application(db_path, _SESSION_A, status="applied")
    # 4 more sessions in the same city → 5 total (at k-threshold).
    for i in range(4):
        sid = f"extra-{i:08d}-bbbb-cccc-dddd-eeeeeeeeeeee"
        _seed_extra_session(db_path, sid, city=_CITY_A)
        _seed_application(db_path, sid, status="applied")

    resp = client.get(
        f"/api/job-applications/community-funnel?token={_TOKEN_A}",
    )
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, dict)
    assert "__all__" in body
    # k-threshold met → not suppressed
    cell = body["__all__"]
    assert cell.get("suppressed") is not True


def test_community_funnel_suppresses_small_cells(
    client: TestClient, db_path: str,
) -> None:
    """Only session A in city → 1 distinct session → suppressed."""
    _seed_application(db_path, _SESSION_A, status="applied")
    resp = client.get(
        f"/api/job-applications/community-funnel?token={_TOKEN_A}",
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["__all__"].get("suppressed") is True
    assert body["__all__"].get("reason") == "k_anonymity_min_5"


def test_community_funnel_city_scope(
    client: TestClient, db_path: str,
) -> None:
    """Session B's fort-worth data must not leak into session A's montgomery query."""
    # Session A + 4 more in montgomery → above k-threshold
    _seed_application(db_path, _SESSION_A, status="applied")
    for i in range(4):
        sid = f"mont-{i:08d}-bbbb-cccc-dddd-eeeeeeeeeeee"
        _seed_extra_session(db_path, sid, city=_CITY_A)
        _seed_application(db_path, sid, status="applied")

    # Session B + 10 fort-worth sessions with offers (must NOT show up)
    _seed_application(db_path, _SESSION_B, status="offer")
    for i in range(10):
        sid = f"fw-{i:08d}-bbbb-cccc-dddd-eeeeeeeeeeee"
        _seed_extra_session(db_path, sid, city=_CITY_B)
        _seed_application(db_path, sid, status="offer")

    resp = client.get(
        f"/api/job-applications/community-funnel?token={_TOKEN_A}",
    )
    assert resp.status_code == 200
    cell = resp.json()["__all__"]
    # Session A's city-scoped cell must show 5 applied + 0 offer.
    assert cell["counts"]["applied"] == 5
    assert cell["counts"]["offer"] == 0


def test_community_funnel_requires_token(client: TestClient) -> None:
    resp = client.get("/api/job-applications/community-funnel")
    assert resp.status_code == 422


def test_community_funnel_invalid_token(client: TestClient) -> None:
    resp = client.get(
        "/api/job-applications/community-funnel?token=nope",
    )
    assert resp.status_code == 401


# -------------------- Route resolution / collision --------------------


def test_no_collision_with_existing_api_jobs_endpoint(
    db_path: str, monkeypatch,
) -> None:
    """/api/jobs/{job_id} and /api/job-applications/{id} must resolve to
    distinct handlers with distinct response shapes. Critical regression
    test for the v2 review blocker.

    Verified via the FastAPI routing table + a behavioural probe on the
    `/api/job-applications` side; does not invoke `/api/jobs/{id}`
    directly (that handler depends on a live async SQLAlchemy session
    which CI runners don't provision).
    """
    from app.routes import jobs as jobs_route
    monkeypatch.setattr(
        jobs_applications_route, "_resolve_db_path", lambda: db_path,
    )
    app = FastAPI()
    app.include_router(jobs_route.router)
    app.include_router(jobs_applications_route.router)

    # Contract check 1: distinct prefixes — /api/jobs vs /api/job-applications.
    jobs_paths = {
        r.path for r in jobs_route.router.routes if hasattr(r, "path")
    }
    app_paths = {
        r.path for r in jobs_applications_route.router.routes
        if hasattr(r, "path")
    }
    assert all(p.startswith("/api/jobs") for p in jobs_paths), jobs_paths
    assert all(p.startswith("/api/job-applications") for p in app_paths), app_paths
    assert not (jobs_paths & app_paths), (
        f"collision: same path in both routers: {jobs_paths & app_paths}"
    )

    # Contract check 2: the PATCH /api/job-applications/{id} route resolves
    # to the jobs_applications handler (not jobs.get_job). Probing via PATCH
    # /api/jobs/9999 → 405 proves /api/jobs doesn't accept PATCH; probing
    # /api/job-applications/9999 with a bogus id → our handler returns 404.
    local_client = TestClient(app)
    resp_patch_jobs = local_client.patch("/api/jobs/9999", json={})
    resp_patch_app = local_client.patch(
        f"/api/job-applications/9999?token={_TOKEN_A}",
        json={"status": "applied"},
    )
    assert resp_patch_jobs.status_code == 405  # method not allowed on jobs
    assert resp_patch_app.status_code == 404  # our handler → not-found


def test_router_registered_in_all_routers() -> None:
    from app.routes import all_routers
    assert jobs_applications_route.router in all_routers

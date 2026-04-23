"""Tests for the appointments API router (T12.10).

Covers all nine endpoints:
- GET /api/appointments?session_id=X
- POST /api/appointments
- GET /api/appointments/{id}
- PATCH /api/appointments/{id}
- DELETE /api/appointments/{id}
- POST /api/appointments/{id}/attended
- POST /api/appointments/{id}/missed
- GET /api/appointments/upcoming?session_id=X&days=7
- POST /api/appointments/from-pathway?session_id=X

Auth contract: token query-param -> feedback_tokens table. For endpoints
that reference a specific appointment id, the route also verifies that
`appointment.session_id` matches the authenticated session (403 otherwise).
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core import events
from app.core.migrations import runner
from app.routes import appointments as appointments_route

_SESSION_A = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
_SESSION_B = "bbbbbbbb-cccc-dddd-eeee-ffffffffffff"
_TOKEN_A = "tok-aaaaa"
_TOKEN_B = "tok-bbbbb"


# -------------------- Fixtures --------------------


@pytest.fixture(autouse=True)
def _isolate_event_bus() -> None:
    events.clear_all_subscribers()
    yield
    events.clear_all_subscribers()


@pytest.fixture
def db_path(tmp_path: Path) -> str:
    path = str(tmp_path / "appts_api.db")
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
        conn.execute(
            "INSERT INTO sessions (id, created_at, barriers, expires_at) "
            "VALUES (?, ?, ?, ?)",
            (session_id, now_iso, "[]", expires_iso),
        )
        conn.execute(
            "INSERT INTO feedback_tokens (token, session_id, created_at, expires_at) "
            "VALUES (?, ?, ?, ?)",
            (token, session_id, now_iso, expires_iso),
        )
        conn.commit()
    finally:
        conn.close()


@pytest.fixture
def client(db_path: str, monkeypatch) -> TestClient:
    monkeypatch.setattr(
        appointments_route, "_resolve_db_path", lambda: db_path,
    )
    app = FastAPI()
    app.include_router(appointments_route.router)
    return TestClient(app)


def _make_appt_body(
    *,
    session_id: str = _SESSION_A,
    starts_offset_h: int = 24,
    duration_min: int = 60,
    title: str = "DMV visit",
    barrier_link: str | None = "dmv",
) -> dict:
    starts = datetime.now(timezone.utc) + timedelta(hours=starts_offset_h)
    ends = starts + timedelta(minutes=duration_min)
    return {
        "session_id": session_id,
        "type": "dmv",
        "title": title,
        "starts_at": starts.isoformat(),
        "ends_at": ends.isoformat(),
        "location_name": "DMV Office",
        "status": "scheduled",
        "source": "user",
        "barrier_link": barrier_link,
    }


# -------------------- GET /api/appointments --------------------


def test_list_by_session_returns_empty_array_when_none(client: TestClient) -> None:
    resp = client.get(f"/api/appointments?session_id={_SESSION_A}&token={_TOKEN_A}")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_by_session_requires_valid_token(client: TestClient) -> None:
    resp = client.get(f"/api/appointments?session_id={_SESSION_A}&token=bad")
    assert resp.status_code == 401


def test_list_by_session_cross_session_token_returns_403(client: TestClient) -> None:
    resp = client.get(f"/api/appointments?session_id={_SESSION_A}&token={_TOKEN_B}")
    assert resp.status_code == 403


# -------------------- POST /api/appointments --------------------


def test_post_creates_appointment(client: TestClient) -> None:
    resp = client.post(
        f"/api/appointments?token={_TOKEN_A}",
        json=_make_appt_body(),
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["id"] is not None
    assert body["session_id"] == _SESSION_A
    assert body["title"] == "DMV visit"
    assert body["status"] == "scheduled"


def test_post_returns_created_in_list(client: TestClient) -> None:
    client.post(
        f"/api/appointments?token={_TOKEN_A}",
        json=_make_appt_body(),
    )
    resp = client.get(
        f"/api/appointments?session_id={_SESSION_A}&token={_TOKEN_A}",
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_malformed_body_returns_422(client: TestClient) -> None:
    resp = client.post(
        f"/api/appointments?token={_TOKEN_A}",
        json={"session_id": _SESSION_A},  # missing required fields
    )
    assert resp.status_code == 422


def test_post_mismatched_session_returns_403(client: TestClient) -> None:
    """Body.session_id must match the authenticated session."""
    resp = client.post(
        f"/api/appointments?token={_TOKEN_A}",
        json=_make_appt_body(session_id=_SESSION_B),
    )
    assert resp.status_code == 403


# -------------------- GET /api/appointments/{id} --------------------


def test_get_by_id_returns_404_when_missing(client: TestClient) -> None:
    resp = client.get(f"/api/appointments/9999?token={_TOKEN_A}")
    assert resp.status_code == 404


def test_get_by_id_returns_200_with_body(client: TestClient) -> None:
    created = client.post(
        f"/api/appointments?token={_TOKEN_A}",
        json=_make_appt_body(),
    ).json()
    resp = client.get(f"/api/appointments/{created['id']}?token={_TOKEN_A}")
    assert resp.status_code == 200
    assert resp.json()["id"] == created["id"]


def test_cross_session_access_returns_403(client: TestClient) -> None:
    """Session A owns an appointment; Session B's token must not read it."""
    created = client.post(
        f"/api/appointments?token={_TOKEN_A}",
        json=_make_appt_body(),
    ).json()
    resp = client.get(f"/api/appointments/{created['id']}?token={_TOKEN_B}")
    assert resp.status_code == 403


# -------------------- PATCH /api/appointments/{id} --------------------


def test_patch_updates_non_status_fields(client: TestClient) -> None:
    created = client.post(
        f"/api/appointments?token={_TOKEN_A}",
        json=_make_appt_body(),
    ).json()
    resp = client.patch(
        f"/api/appointments/{created['id']}?token={_TOKEN_A}",
        json={"title": "Updated title", "notes": "hello"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["title"] == "Updated title"
    assert body["notes"] == "hello"
    assert body["status"] == "scheduled"  # unchanged


def test_patch_rejects_status_field(client: TestClient) -> None:
    """PATCH must NOT change status — use dedicated endpoints."""
    created = client.post(
        f"/api/appointments?token={_TOKEN_A}",
        json=_make_appt_body(),
    ).json()
    resp = client.patch(
        f"/api/appointments/{created['id']}?token={_TOKEN_A}",
        json={"status": "attended"},
    )
    assert resp.status_code == 400


# -------------------- DELETE /api/appointments/{id} --------------------


def test_delete_marks_cancelled(client: TestClient) -> None:
    created = client.post(
        f"/api/appointments?token={_TOKEN_A}",
        json=_make_appt_body(),
    ).json()
    resp = client.delete(f"/api/appointments/{created['id']}?token={_TOKEN_A}")
    assert resp.status_code == 204
    # Verify status is now cancelled
    get_resp = client.get(f"/api/appointments/{created['id']}?token={_TOKEN_A}")
    assert get_resp.status_code == 200
    assert get_resp.json()["status"] == "cancelled"


# -------------------- POST /{id}/attended --------------------


def test_post_attended_transitions_to_attended(client: TestClient) -> None:
    created = client.post(
        f"/api/appointments?token={_TOKEN_A}",
        json=_make_appt_body(),
    ).json()
    resp = client.post(
        f"/api/appointments/{created['id']}/attended?token={_TOKEN_A}",
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "attended"


def test_post_attended_fails_from_cancelled(client: TestClient) -> None:
    created = client.post(
        f"/api/appointments?token={_TOKEN_A}",
        json=_make_appt_body(),
    ).json()
    client.delete(f"/api/appointments/{created['id']}?token={_TOKEN_A}")
    resp = client.post(
        f"/api/appointments/{created['id']}/attended?token={_TOKEN_A}",
    )
    assert resp.status_code == 409


# -------------------- POST /{id}/missed --------------------


def test_post_missed_transitions_to_missed(client: TestClient) -> None:
    created = client.post(
        f"/api/appointments?token={_TOKEN_A}",
        json=_make_appt_body(),
    ).json()
    resp = client.post(
        f"/api/appointments/{created['id']}/missed?token={_TOKEN_A}",
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "missed"


# -------------------- GET /upcoming --------------------


def test_upcoming_returns_next_N_days(client: TestClient) -> None:
    # 2 within 7 days + 1 in 14 days
    client.post(
        f"/api/appointments?token={_TOKEN_A}",
        json=_make_appt_body(starts_offset_h=24),  # +1 day
    )
    client.post(
        f"/api/appointments?token={_TOKEN_A}",
        json=_make_appt_body(starts_offset_h=24 * 3),  # +3 days
    )
    client.post(
        f"/api/appointments?token={_TOKEN_A}",
        json=_make_appt_body(starts_offset_h=24 * 14),  # +14 days
    )
    resp = client.get(
        f"/api/appointments/upcoming?session_id={_SESSION_A}&days=7&token={_TOKEN_A}",
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 2


# -------------------- POST /from-pathway --------------------


def test_from_pathway_creates_placeholders(client: TestClient, db_path: str) -> None:
    """POST /from-pathway seeds placeholders for pathway-barriers."""
    # Seed barriers into the session row so the route can fetch them.
    _seed_barriers(db_path, _SESSION_A, ["expunction", "dmv_license"])

    resp = client.post(
        f"/api/appointments/from-pathway?session_id={_SESSION_A}&token={_TOKEN_A}&city=montgomery",
    )
    assert resp.status_code == 200
    created = resp.json()
    assert isinstance(created, list)
    assert len(created) == 2
    barrier_links = {appt["barrier_link"] for appt in created}
    assert barrier_links == {"expunction", "dmv_license"}


def test_from_pathway_is_idempotent(client: TestClient, db_path: str) -> None:
    _seed_barriers(db_path, _SESSION_A, ["expunction"])

    first = client.post(
        f"/api/appointments/from-pathway?session_id={_SESSION_A}&token={_TOKEN_A}&city=montgomery",
    )
    assert first.status_code == 200
    assert len(first.json()) == 1

    second = client.post(
        f"/api/appointments/from-pathway?session_id={_SESSION_A}&token={_TOKEN_A}&city=montgomery",
    )
    assert second.status_code == 200
    assert second.json() == []


def _seed_barriers(db_path: str, session_id: str, barriers: list[str]) -> None:
    import json as _json
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "UPDATE sessions SET barriers = ? WHERE id = ?",
            (_json.dumps(barriers), session_id),
        )
        conn.commit()
    finally:
        conn.close()


# -------------------- Router registration --------------------


def test_router_registered_in_all_routers() -> None:
    from app.routes import all_routers
    assert appointments_route.router in all_routers

"""Tests for the engagement API routes (T12.21, S12b).

Covers the four endpoints landed in S12b (preview-digest already shipped
in S12a — see :mod:`tests.test_engagement_preview_route`):

    GET  /api/engagement/events
    POST /api/engagement/preferences
    POST /api/engagement/send-now
    POST /api/engagement/unsubscribe

Carry-over: ``sessions.reminders_enabled`` is NOT a real column; T12.19
established the ``engagement_events`` row pattern (category =
``reminders_auto_disabled``) as the opt-out signal. Both
``POST /preferences`` and ``POST /unsubscribe`` use that same pattern,
so the reminder engine's preflight already honours these writes.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core import events
from app.core.migrations import runner

_SESSION_A = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
_SESSION_B = "bbbbbbbb-cccc-dddd-eeee-ffffffffffff"
_TOKEN_A = "tok-aaaaa"
_TOKEN_B = "tok-bbbbb"
_ADMIN_KEY = "test-admin-key-for-engagement-routes"
_UNSUB_SECRET = "unsub-engagement-route-test-secret-0123456789ab"
_SETTINGS_PATCH = "app.core.auth.get_settings"


# -------------------- Fixtures --------------------


@pytest.fixture(autouse=True)
def _isolate_event_bus() -> None:
    events.clear_all_subscribers()
    yield
    events.clear_all_subscribers()


@pytest.fixture(autouse=True)
def _reset_engagement_rate_limit() -> None:
    """Each test starts with an empty rate-limit window."""
    from app.routes import engagement as eng

    eng._RATE_LIMITER.clear()
    yield
    eng._RATE_LIMITER.clear()


@pytest.fixture
def db_path(tmp_path: Path) -> str:
    path = str(tmp_path / "engagement.db")
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
            "INSERT INTO feedback_tokens "
            "(token, session_id, created_at, expires_at) "
            "VALUES (?, ?, ?, ?)",
            (token, session_id, now_iso, expires_iso),
        )
        conn.commit()
    finally:
        conn.close()


def _seed_event(
    path: str, session_id: str, category: str, payload: str = "{}",
) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            "INSERT INTO engagement_events "
            "(session_id, category, payload_json, created_at) "
            "VALUES (?, ?, ?, ?)",
            (session_id, category, payload, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
    finally:
        conn.close()


def _has_auto_disabled_row(path: str, session_id: str) -> bool:
    conn = sqlite3.connect(path)
    try:
        row = conn.execute(
            "SELECT 1 FROM engagement_events "
            "WHERE session_id = ? AND category = 'reminders_auto_disabled' "
            "LIMIT 1",
            (session_id,),
        ).fetchone()
    finally:
        conn.close()
    return row is not None


@pytest.fixture
def client(db_path: str, monkeypatch) -> TestClient:
    from app.routes import engagement as eng

    monkeypatch.setattr(eng, "_resolve_db_path", lambda: db_path)
    monkeypatch.setenv("UNSUBSCRIBE_TOKEN_SECRET", _UNSUB_SECRET)
    monkeypatch.delenv("UNSUBSCRIBE_TOKEN_SECRET_OLD", raising=False)

    settings_stub = MagicMock()
    settings_stub.admin_api_key = _ADMIN_KEY

    app = FastAPI()
    app.include_router(eng.router)

    with patch(_SETTINGS_PATCH, return_value=settings_stub):
        yield TestClient(app)


# -------------------- GET /events --------------------


def test_events_empty_returns_empty_list(client: TestClient) -> None:
    """Session with no engagement_events rows returns events=[]."""
    resp = client.get(
        f"/api/engagement/events?session_id={_SESSION_A}&token={_TOKEN_A}",
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body == {"events": []}


def test_events_returns_session_events(
    client: TestClient, db_path: str,
) -> None:
    """Engagement events rows for the session appear in the response."""
    _seed_event(db_path, _SESSION_A, "reminder_sent", '{"level": "soft"}')
    _seed_event(db_path, _SESSION_A, "digest_sent")

    resp = client.get(
        f"/api/engagement/events?session_id={_SESSION_A}&token={_TOKEN_A}",
    )
    assert resp.status_code == 200
    body = resp.json()
    categories = [e["category"] for e in body["events"]]
    assert "reminder_sent" in categories
    assert "digest_sent" in categories


def test_events_scoped_per_session(
    client: TestClient, db_path: str,
) -> None:
    """Session A must not see Session B's engagement events."""
    _seed_event(db_path, _SESSION_B, "reminder_sent")
    resp = client.get(
        f"/api/engagement/events?session_id={_SESSION_A}&token={_TOKEN_A}",
    )
    assert resp.status_code == 200
    assert resp.json() == {"events": []}


def test_events_invalid_token_401(client: TestClient) -> None:
    resp = client.get(
        f"/api/engagement/events?session_id={_SESSION_A}&token=bad",
    )
    assert resp.status_code == 401


def test_events_cross_session_403(client: TestClient) -> None:
    """Session A's token must not list Session B's events."""
    resp = client.get(
        f"/api/engagement/events?session_id={_SESSION_B}&token={_TOKEN_A}",
    )
    assert resp.status_code == 403


# -------------------- POST /preferences --------------------


def test_preferences_disable_writes_auto_disabled_row(
    client: TestClient, db_path: str,
) -> None:
    """Setting reminders_enabled=False writes the opt-out signal row."""
    resp = client.post(
        f"/api/engagement/preferences?session_id={_SESSION_A}&token={_TOKEN_A}",
        json={"reminders_enabled": False},
    )
    assert resp.status_code == 200
    assert resp.json()["reminders_enabled"] is False
    assert _has_auto_disabled_row(db_path, _SESSION_A)


def test_preferences_enable_clears_auto_disabled_row(
    client: TestClient, db_path: str,
) -> None:
    """Setting reminders_enabled=True clears any prior opt-out row."""
    _seed_event(db_path, _SESSION_A, "reminders_auto_disabled")
    assert _has_auto_disabled_row(db_path, _SESSION_A)

    resp = client.post(
        f"/api/engagement/preferences?session_id={_SESSION_A}&token={_TOKEN_A}",
        json={"reminders_enabled": True},
    )
    assert resp.status_code == 200
    assert resp.json()["reminders_enabled"] is True
    assert not _has_auto_disabled_row(db_path, _SESSION_A)


def test_preferences_cross_session_403(client: TestClient) -> None:
    resp = client.post(
        f"/api/engagement/preferences?session_id={_SESSION_B}&token={_TOKEN_A}",
        json={"reminders_enabled": False},
    )
    assert resp.status_code == 403


def test_preferences_invalid_token_401(client: TestClient) -> None:
    resp = client.post(
        f"/api/engagement/preferences?session_id={_SESSION_A}&token=bad",
        json={"reminders_enabled": False},
    )
    assert resp.status_code == 401


# -------------------- POST /send-now (admin) --------------------


def test_send_now_missing_admin_key_422(client: TestClient) -> None:
    resp = client.post(
        "/api/engagement/send-now",
        json={"session_id": _SESSION_A},
    )
    # FastAPI raises 422 when the X-Admin-Key Header is missing.
    assert resp.status_code in (401, 403, 422)


def test_send_now_wrong_admin_key_403(client: TestClient) -> None:
    resp = client.post(
        "/api/engagement/send-now",
        headers={"X-Admin-Key": "wrong"},
        json={"session_id": _SESSION_A},
    )
    assert resp.status_code == 403


def test_send_now_success_invokes_reminder_engine(client: TestClient) -> None:
    """A valid admin call dispatches via the reminder_engine."""
    from app.modules.engagement.reminder_engine import ReminderDispatchResult
    from app.routes import engagement as eng

    fake_result = ReminderDispatchResult(
        success=True, skipped_reason=None,
        category="reminder_soft", message_id="msg-123",
    )
    with patch.object(
        eng, "_dispatch_send_now", return_value=fake_result,
    ) as mock_send:
        resp = client.post(
            "/api/engagement/send-now",
            headers={"X-Admin-Key": _ADMIN_KEY},
            json={"session_id": _SESSION_A},
        )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["success"] is True
    assert body["message_id"] == "msg-123"
    mock_send.assert_called_once()


def test_send_now_rate_limit_blocks_4th_call(client: TestClient) -> None:
    """4th send-now in one hour for the same admin token returns 429."""
    from app.modules.engagement.reminder_engine import ReminderDispatchResult
    from app.routes import engagement as eng

    fake_result = ReminderDispatchResult(
        success=True, skipped_reason=None,
        category="reminder_soft", message_id="m",
    )
    with patch.object(eng, "_dispatch_send_now", return_value=fake_result):
        statuses = []
        for _ in range(4):
            resp = client.post(
                "/api/engagement/send-now",
                headers={"X-Admin-Key": _ADMIN_KEY},
                json={"session_id": _SESSION_A},
            )
            statuses.append(resp.status_code)
    assert statuses[:3] == [200, 200, 200]
    assert statuses[3] == 429


# -------------------- POST /unsubscribe --------------------


def test_unsubscribe_round_trip_disables_reminders(
    client: TestClient, db_path: str,
) -> None:
    """Valid signed token writes the auto-disabled row."""
    from app.modules.engagement import unsubscribe_tokens

    token = unsubscribe_tokens.sign(_SESSION_A)
    resp = client.post(
        "/api/engagement/unsubscribe", json={"token": token},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["reminders_enabled"] is False
    assert _has_auto_disabled_row(db_path, _SESSION_A)


def test_unsubscribe_invalid_token_401(client: TestClient) -> None:
    resp = client.post(
        "/api/engagement/unsubscribe", json={"token": "garbage"},
    )
    assert resp.status_code == 401


def test_unsubscribe_replay_401(
    client: TestClient, db_path: str,
) -> None:
    """Second use of the same unsubscribe token is rejected."""
    from app.modules.engagement import unsubscribe_tokens

    token = unsubscribe_tokens.sign(_SESSION_A)
    first = client.post(
        "/api/engagement/unsubscribe", json={"token": token},
    )
    assert first.status_code == 200
    second = client.post(
        "/api/engagement/unsubscribe", json={"token": token},
    )
    assert second.status_code == 401


def test_unsubscribe_blocks_reminder_engine(
    client: TestClient, db_path: str,
) -> None:
    """After unsubscribe, the reminder engine's preflight skips the session."""
    from app.modules.engagement import unsubscribe_tokens
    from app.modules.engagement.reminder_engine import _is_reminders_auto_disabled

    token = unsubscribe_tokens.sign(_SESSION_A)
    resp = client.post(
        "/api/engagement/unsubscribe", json={"token": token},
    )
    assert resp.status_code == 200
    assert _is_reminders_auto_disabled(db_path, _SESSION_A) is True


# -------------------- Router registration --------------------


def test_router_registered_in_all_routers() -> None:
    from app.routes import all_routers, engagement

    assert engagement.router in all_routers

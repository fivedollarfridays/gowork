"""Tests for the engagement preview-digest API endpoint (T12.21a).

Covers the single endpoint landed in S12a:

    GET /api/engagement/preview-digest?session_id=X&token=Y[&for_date=YYYY-MM-DD]

Auth contract mirrors the appointments router: token validated against
``feedback_tokens``, and session_id must match the token's owning session
(403 otherwise). The endpoint renders today's digest via T12.20
``compose_digest`` and does NOT send email.

Remaining four engagement endpoints (events, preferences, send-now,
unsubscribe) land in S12b T12.21.
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
from app.routes import engagement_preview as engagement_preview_route

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
    path = str(tmp_path / "engagement_preview.db")
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


@pytest.fixture
def client(db_path: str, monkeypatch) -> TestClient:
    monkeypatch.setattr(
        engagement_preview_route, "_resolve_db_path", lambda: db_path,
    )
    app = FastAPI()
    app.include_router(engagement_preview_route.router)
    return TestClient(app)


# -------------------- Core response shape --------------------


def test_returns_html_and_text(client: TestClient) -> None:
    """Authenticated session returns 200 with html + text keys."""
    resp = client.get(
        f"/api/engagement/preview-digest"
        f"?session_id={_SESSION_A}&token={_TOKEN_A}",
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "html" in body
    assert "text" in body
    assert isinstance(body["html"], str) and body["html"]
    assert isinstance(body["text"], str) and body["text"]


def test_subject_present(client: TestClient) -> None:
    """Response includes a subject line."""
    resp = client.get(
        f"/api/engagement/preview-digest"
        f"?session_id={_SESSION_A}&token={_TOKEN_A}",
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "subject" in body
    assert body["subject"].startswith("[MontGoWork]")


def test_section_counts_present(client: TestClient) -> None:
    """Response has a section_counts dict with all four section ids."""
    resp = client.get(
        f"/api/engagement/preview-digest"
        f"?session_id={_SESSION_A}&token={_TOKEN_A}",
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "section_counts" in body
    counts = body["section_counts"]
    assert isinstance(counts, dict)
    # compose_digest always emits all four keys for observability
    assert set(counts.keys()) == {"yesterday", "today", "week", "stall"}


# -------------------- Auth --------------------


def test_missing_token_returns_422(client: TestClient) -> None:
    """FastAPI returns 422 when the required `token` query param is absent."""
    resp = client.get(
        f"/api/engagement/preview-digest?session_id={_SESSION_A}",
    )
    assert resp.status_code == 422


def test_invalid_token_returns_401(client: TestClient) -> None:
    resp = client.get(
        f"/api/engagement/preview-digest"
        f"?session_id={_SESSION_A}&token=bad",
    )
    assert resp.status_code == 401


def test_cross_session_returns_403(client: TestClient) -> None:
    """Session A's token must not preview session B's digest."""
    resp = client.get(
        f"/api/engagement/preview-digest"
        f"?session_id={_SESSION_B}&token={_TOKEN_A}",
    )
    assert resp.status_code == 403


# -------------------- Empty-state + for_date --------------------


def test_empty_state_digest_returns_200(client: TestClient) -> None:
    """Fresh session with no signals renders a minimal digest, not an error."""
    resp = client.get(
        f"/api/engagement/preview-digest"
        f"?session_id={_SESSION_A}&token={_TOKEN_A}",
    )
    assert resp.status_code == 200
    body = resp.json()
    # All four section counts should be zero for a fresh session
    assert body["section_counts"] == {
        "yesterday": 0, "today": 0, "week": 0, "stall": 0,
    }
    # HTML should include the empty-state placeholder
    assert "Nothing new today" in body["html"]


def test_for_date_parameter_accepted(client: TestClient) -> None:
    """?for_date=YYYY-MM-DD is honored (reflected in subject line)."""
    resp = client.get(
        f"/api/engagement/preview-digest"
        f"?session_id={_SESSION_A}&token={_TOKEN_A}"
        f"&for_date=2026-04-22",
    )
    assert resp.status_code == 200
    body = resp.json()
    # Subject uses strftime("%A, %b %d"); 2026-04-22 is a Wednesday
    assert "Wednesday" in body["subject"]
    assert "Apr 22" in body["subject"]


def test_for_date_invalid_returns_400(client: TestClient) -> None:
    """Non-ISO for_date returns 400 with a clear message."""
    resp = client.get(
        f"/api/engagement/preview-digest"
        f"?session_id={_SESSION_A}&token={_TOKEN_A}"
        f"&for_date=not-a-date",
    )
    assert resp.status_code == 400


def test_for_date_defaults_to_today_city_local(client: TestClient) -> None:
    """When for_date is omitted, today's city-local date drives the subject."""
    from app.core.day_boundary import current_work_date
    from app.core.config import get_settings

    resp = client.get(
        f"/api/engagement/preview-digest"
        f"?session_id={_SESSION_A}&token={_TOKEN_A}",
    )
    assert resp.status_code == 200
    body = resp.json()
    today_city_local = current_work_date(get_settings().city)
    expected_label = today_city_local.strftime("%b %d")
    assert expected_label in body["subject"]


# -------------------- Router registration --------------------


def test_router_registered_in_all_routers() -> None:
    from app.routes import all_routers
    assert engagement_preview_route.router in all_routers

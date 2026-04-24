"""Shared helpers for advisor inbox tests (T12.31).

Extracted from ``test_advisor_inbox.py`` / ``test_advisor_auth.py`` so
neither test file ever crosses the 400-line architecture limit. All
helpers are pure — no pytest fixtures live here; the two test modules
declare their own ``migrated_db`` + ``reset_rate_limiter`` fixtures.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

_NOW = datetime(2026, 4, 23, 12, 0, tzinfo=timezone.utc)
_TOKEN = "mw_adv_test0000000000000000000000000"

# Outcomes-tracker validates session ids as UUIDs; use fixed UUID strings
# so every test's seeded sessions round-trip through the live reader.
_SID_MTG_1 = "11111111-1111-4111-8111-111111111111"
_SID_MTG_2 = "22222222-2222-4222-8222-222222222222"
_SID_FW_1 = "55555555-5555-4555-8555-555555555555"
_SID_DEMO = "66666666-6666-4666-8666-666666666666"
_SID_REAL = "77777777-7777-4777-8777-777777777777"
_SID_RATE = "88888888-8888-4888-8888-888888888888"
_SID_NOTE = "99999999-9999-4999-8999-999999999999"


def insert_advisor_token(
    db_path: str, token_plaintext: str, advisor_id: str, city: str,
    *, revoked: bool = False, expires_at: datetime | None = None,
) -> None:
    """Insert an advisor_tokens row mirroring the issuance CLI."""
    from app.core.advisor_auth import hash_token
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO advisor_tokens "
            "(token_hash, advisor_id, city, issued_at, revoked_at, expires_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                hash_token(token_plaintext),
                advisor_id,
                city,
                _NOW.isoformat(),
                _NOW.isoformat() if revoked else None,
                expires_at.isoformat() if expires_at else None,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def seed_session(
    db_path: str, session_id: str, *,
    demo: bool = False, profile_email: str | None = "worker@example.com",
) -> None:
    """Seed a minimal session row."""
    profile = json.dumps(
        {"email": profile_email, "first_name": "Worker"}
        if profile_email else {},
    )
    exp = (_NOW + timedelta(days=30)).isoformat()
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO sessions (id, created_at, barriers, profile, "
            "expires_at, demo) VALUES (?, ?, ?, ?, ?, ?)",
            (session_id, _NOW.isoformat(), "[]", profile, exp, 1 if demo else 0),
        )
        conn.commit()
    finally:
        conn.close()


def seed_outcome_city(
    db_path: str, session_id: str, city: str,
    *, when: datetime | None = None,
) -> None:
    """Insert one outcomes_records row carrying a city tag."""
    ts = (when or _NOW).isoformat()
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO outcomes_records (session_id, event_type, "
            "payload_json, created_at) VALUES (?, ?, ?, ?)",
            (session_id, "appointment_attended",
             json.dumps({"city": city}), ts),
        )
        conn.commit()
    finally:
        conn.close()


def seed_stalled_session(
    db_path: str, session_id: str, city: str,
    *, days_ago: int, demo: bool = False,
) -> None:
    """Seed a session + one stale outcome so the stall detector trips."""
    seed_session(db_path, session_id, demo=demo)
    seed_outcome_city(
        db_path, session_id, city,
        when=_NOW - timedelta(days=days_ago),
    )


def build_client(
    migrated_db: str, monkeypatch: pytest.MonkeyPatch,
) -> TestClient:
    """TestClient mounting the advisor_inbox router with a temp DB."""
    from app.routes import advisor_inbox
    monkeypatch.setattr(
        advisor_inbox, "_resolve_db_path", lambda: migrated_db,
    )
    app = FastAPI()
    app.include_router(advisor_inbox.router)
    return TestClient(app)


def stub_send_advisor_note(
    monkeypatch: pytest.MonkeyPatch, calls: list[dict] | None = None,
) -> None:
    """Monkeypatch reminder_engine.send_advisor_note to a test stub."""
    from app.modules.engagement import reminder_engine

    def _fake(session_id: str, message: str, *, db_path, now=None):
        if calls is not None:
            calls.append({"session_id": session_id, "message": message})

        class _R:
            success = True
            skipped_reason = None
            category = "advisor_note"
            message_id = "msg-1"
        return _R()

    monkeypatch.setattr(
        reminder_engine, "send_advisor_note", _fake, raising=False,
    )


def read_advisor_action_rows(
    db_path: str, session_id: str,
) -> list[dict]:
    """Return engagement_events advisor_action payloads for a session."""
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT payload_json FROM engagement_events "
            "WHERE session_id = ? AND category = 'advisor_action'",
            (session_id,),
        ).fetchall()
    finally:
        conn.close()
    return [json.loads(r[0]) for r in rows]


__all__ = [
    "_NOW",
    "_SID_DEMO", "_SID_FW_1", "_SID_MTG_1", "_SID_MTG_2",
    "_SID_NOTE", "_SID_RATE", "_SID_REAL", "_TOKEN",
    "build_client",
    "insert_advisor_token",
    "read_advisor_action_rows",
    "seed_outcome_city",
    "seed_session",
    "seed_stalled_session",
    "stub_send_advisor_note",
]

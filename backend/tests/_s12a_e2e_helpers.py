"""Helpers for the S12a end-to-end integration tests (T12.32).

Extracted from ``test_s12a_worker_companion_e2e.py`` to keep that
module under the 600-line / 30-import / 50-line-per-function arch
limits. Pure test utilities — no project production imports beyond
the data-layer seeds tests need.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.integrations.email.core import EmailSendResult
from app.routes import appointments as appointments_route
from app.routes import engagement_preview as engagement_preview_route
from app.routes import jobs as jobs_route
from app.routes import jobs_applications as jobs_applications_route


# City_tag row is inserted at -200d so it never shows up inside the
# stall detector's 90-day lookback window.
_CITY_TAG_AGE_DAYS = 200


def _build_profile(
    email: str | None, cleared_barriers: list[str] | None,
) -> dict[str, Any]:
    """Assemble the JSON blob stored in ``sessions.profile``."""
    profile: dict[str, Any] = {"first_name": "Worker"}
    if email is not None:
        profile["email"] = email
    if cleared_barriers is not None:
        profile["cleared_barriers"] = cleared_barriers
    return profile


def _insert_session_row(
    conn: sqlite3.Connection, session_id: str, now_iso: str,
    expires_iso: str, barriers: list[str], profile: dict[str, Any],
) -> None:
    conn.execute(
        "INSERT INTO sessions "
        "(id, created_at, barriers, profile, expires_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (
            session_id, now_iso, json.dumps(barriers),
            json.dumps(profile), expires_iso,
        ),
    )


def _insert_token_row(
    conn: sqlite3.Connection, token: str, session_id: str,
    now_iso: str, expires_iso: str,
) -> None:
    conn.execute(
        "INSERT INTO feedback_tokens "
        "(token, session_id, created_at, expires_at) "
        "VALUES (?, ?, ?, ?)",
        (token, session_id, now_iso, expires_iso),
    )


def _insert_city_tag(
    conn: sqlite3.Connection, session_id: str, city: str, ts_iso: str,
) -> None:
    conn.execute(
        "INSERT INTO outcomes_records "
        "(session_id, event_type, payload_json, created_at) "
        "VALUES (?, ?, ?, ?)",
        (session_id, "city_tag", json.dumps({"city": city}), ts_iso),
    )


def seed_session(
    db_path: str,
    session_id: str,
    token: str,
    *,
    barriers: list[str] | None = None,
    city: str | None = None,
    email: str | None = "worker@example.com",
    cleared_barriers: list[str] | None = None,
) -> None:
    """Insert session + feedback_token; optional city tag + profile email.

    The city_tag outcome row is written ``_CITY_TAG_AGE_DAYS`` in the
    past — outside the stall detector's 90-day lookback window — so it
    never counts as a recent progress signal. This matches real-world
    semantics: city tagging happens at session inception, not as
    ongoing worker activity.
    """
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()
    expires_iso = (now + timedelta(days=30)).isoformat()
    city_tag_iso = (now - timedelta(days=_CITY_TAG_AGE_DAYS)).isoformat()
    profile = _build_profile(email, cleared_barriers)

    conn = sqlite3.connect(db_path)
    try:
        _insert_session_row(
            conn, session_id, now_iso, expires_iso,
            barriers or [], profile,
        )
        _insert_token_row(conn, token, session_id, now_iso, expires_iso)
        if city is not None:
            _insert_city_tag(conn, session_id, city, city_tag_iso)
        conn.commit()
    finally:
        conn.close()


def insert_outcome(
    db_path: str, session_id: str, event_type: str,
    *, created_at: datetime | None = None, city: str | None = None,
) -> None:
    """Low-level outcomes_records insert with explicit created_at."""
    ts = (created_at or datetime.now(timezone.utc)).isoformat()
    payload: dict[str, Any] = {}
    if city is not None:
        payload["city"] = city
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO outcomes_records "
            "(session_id, event_type, payload_json, created_at) "
            "VALUES (?, ?, ?, ?)",
            (session_id, event_type, json.dumps(payload), ts),
        )
        conn.commit()
    finally:
        conn.close()


def install_sendgrid_spy(monkeypatch: pytest.MonkeyPatch) -> list[dict]:
    """Replace scripts.nightly_digest.send_transactional with a recorder."""
    calls: list[dict] = []

    def _fake_send(
        to: str, subject: str, html: str, text_fallback: str,
        category: str, *, session_id: str | None = None, db_path: Any = None,
    ) -> EmailSendResult:
        calls.append({
            "to": to, "subject": subject, "category": category,
            "session_id": session_id,
        })
        return EmailSendResult(
            success=True, message_id="mid-spy",
            attempt_count=1, skipped_reason=None,
        )

    import scripts.nightly_digest as nd
    monkeypatch.setattr(nd, "send_transactional", _fake_send)
    return calls


def build_appts_client(
    db_path: str, monkeypatch: pytest.MonkeyPatch,
) -> TestClient:
    """Minimal FastAPI app with appointments router, DB-patched."""
    monkeypatch.setattr(
        appointments_route, "_resolve_db_path", lambda: db_path,
    )
    app = FastAPI()
    app.include_router(appointments_route.router)
    return TestClient(app)


def build_multi_router_client(
    db_path: str, monkeypatch: pytest.MonkeyPatch,
) -> TestClient:
    """FastAPI app with multiple S12a routers mounted + DB patched everywhere."""
    monkeypatch.setattr(
        appointments_route, "_resolve_db_path", lambda: db_path,
    )
    monkeypatch.setattr(
        engagement_preview_route, "_resolve_db_path", lambda: db_path,
    )
    monkeypatch.setattr(
        jobs_applications_route, "_resolve_db_path", lambda: db_path,
    )
    app = FastAPI()
    app.include_router(appointments_route.router)
    app.include_router(engagement_preview_route.router)
    app.include_router(jobs_applications_route.router)
    app.include_router(jobs_route.router)
    return TestClient(app)


async def seed_session_async(
    test_engine, session_id: str, barriers: list[str], auth_token: str,
) -> None:
    """Seed a session + token via the async engine.

    Ported from ``test_barrier_linker._seed_session_via_engine`` for the
    two-caller pathway hook contract test (Contract 2), which needs the
    conftest ``client`` + ``test_engine`` fixtures to drive the real
    async pathway router.
    """
    from sqlalchemy import text  # noqa: PLC0415 — async-only import scope

    from app.core.database import get_async_session_factory  # noqa: PLC0415

    factory = get_async_session_factory()
    async with factory() as db:
        now = datetime.now(timezone.utc)
        expires = (now + timedelta(days=30)).isoformat()
        plan = json.dumps({
            "plan_id": "test", "session_id": session_id,
            "barriers": [], "immediate_next_steps": ["Go"],
        })
        await db.execute(
            text(
                "INSERT INTO sessions (id, created_at, barriers, plan, "
                "expires_at) VALUES (:id, :ts, :b, :p, :exp)"
            ),
            {"id": session_id, "ts": now.isoformat(),
             "b": json.dumps(barriers), "p": plan, "exp": expires},
        )
        await db.execute(
            text(
                "INSERT INTO feedback_tokens "
                "(token, session_id, created_at, expires_at) "
                "VALUES (:tok, :sid, :ts, :exp)"
            ),
            {"tok": auth_token, "sid": session_id,
             "ts": now.isoformat(), "exp": expires},
        )
        await db.commit()


__all__ = [
    "build_appts_client",
    "build_multi_router_client",
    "insert_outcome",
    "install_sendgrid_spy",
    "seed_session",
    "seed_session_async",
]

# Silence Path import warning — kept in case future helpers need it.
_ = Path

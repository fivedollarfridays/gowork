"""Helpers for the appointments API router (T12.10).

Extracted from :mod:`app.routes.appointments` to stay under the
architecture 12-functions-per-file limit. Each helper is synchronous
and operates directly on the sqlite file used by
:mod:`app.modules.appointments.persistence`.
"""

from __future__ import annotations

import json
import sqlite3

from fastapi import HTTPException

from app.integrations.email.core import resolve_db_path as _resolve_email_db_path
from app.modules.appointments import scheduler
from app.modules.appointments.types import Appointment


def resolve_db_path() -> str:
    """Return the sqlite DB path for appointment CRUD.

    Delegates to the email module's resolver (which reads
    ``settings.database_url``) so route + integration share a single
    source of truth. Test harnesses should monkeypatch this function.
    """
    path = _resolve_email_db_path(None)
    if path is None:
        raise HTTPException(status_code=503, detail="Database path unresolved")
    return str(path)


def verify_token(db_path: str, session_id: str, token: str) -> None:
    """Raise 401 / 403 unless the token is valid for the given session.

    Mirrors the semantics of ``app.core.auth.require_session_token`` but
    uses sync sqlite3 so the appointments router never needs an async
    session. The feedback_tokens table is shared with the async routes.
    """
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute(
            "SELECT session_id, expires_at FROM feedback_tokens WHERE token = ?",
            (token,),
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    stored_session, expires_at = row[0], row[1]
    if _is_expired(expires_at):
        raise HTTPException(status_code=401, detail="Token expired")
    if stored_session != session_id:
        raise HTTPException(status_code=403, detail="Token does not match session")


def _is_expired(expires_at: str | None) -> bool:
    """Return True iff expires_at (ISO-8601) is in the past."""
    if not expires_at:
        return False
    from datetime import datetime, timezone
    try:
        parsed = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
    except ValueError:
        return False
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed <= datetime.now(timezone.utc)


def resolve_session_from_token(db_path: str, token: str) -> str:
    """Return the session_id owning a token, or raise 401."""
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute(
            "SELECT session_id, expires_at FROM feedback_tokens WHERE token = ?",
            (token,),
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    if _is_expired(row[1]):
        raise HTTPException(status_code=401, detail="Token expired")
    return row[0]


def load_owned_appointment(
    appointment_id: int, session_id: str, *, db_path: str,
) -> Appointment:
    """Fetch an appointment; raise 404 if missing, 403 if cross-session."""
    appt = scheduler.get(appointment_id, db_path=db_path)
    if appt is None:
        raise HTTPException(status_code=404, detail="Appointment not found")
    if appt.session_id != session_id:
        raise HTTPException(
            status_code=403, detail="Appointment belongs to another session",
        )
    return appt


def fetch_session_barriers(db_path: str, session_id: str) -> list[str]:
    """Return the `barriers` JSON array from the sessions row."""
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute(
            "SELECT barriers FROM sessions WHERE id = ?", (session_id,),
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail="Session not found")
    raw = row[0] or "[]"
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError):
        return []
    return [str(b) for b in parsed] if isinstance(parsed, list) else []


def fetch_session_city(db_path: str, session_id: str) -> str:
    """Return the best-effort city slug for a session.

    Sessions do not currently carry a `city` column; tenants fall back
    to the app-level default from ``settings.city``. Kept as its own
    helper so a future per-session city override has a single place to
    change.
    """
    from app.core.config import get_settings
    return get_settings().city


__all__ = [
    "fetch_session_barriers",
    "fetch_session_city",
    "load_owned_appointment",
    "resolve_db_path",
    "resolve_session_from_token",
    "verify_token",
]

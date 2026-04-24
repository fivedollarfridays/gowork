"""Engagement API routes (T12.21, S12b).

Four endpoints — preview-digest already shipped via S12a T12.21a in
:mod:`app.routes.engagement_preview` and is NOT re-implemented here:

    GET  /api/engagement/events        — list session-scoped events
    POST /api/engagement/preferences   — toggle reminders_enabled
    POST /api/engagement/send-now      — admin, rate-limited 3/hr
    POST /api/engagement/unsubscribe   — public, signed-token gated

Carry-over (documented in T12.19): ``sessions.reminders_enabled`` is
NOT a real column. The opt-out signal is an ``engagement_events`` row
with ``category = 'reminders_auto_disabled'`` (T12.19 reminder engine
already honours this row in its preflight). Both ``POST /preferences``
and ``POST /unsubscribe`` write/clear that row instead of mutating any
hypothetical column. Adding a real column is out of scope for T12.21.

Rate limiter for ``send-now`` is in-process (per-worker) — same shape
as :mod:`app.routes.admin_flags` but with a 3/hour cap. Replacing this
with Redis is a sprint-12c-or-later concern.

Helpers live in :func:`_resolve_db_path` (monkeypatched by tests) and
:func:`_dispatch_send_now` (monkeypatched in tests so we never hit
SendGrid in unit tests).
"""

from __future__ import annotations

import json
import logging
import sqlite3
from datetime import datetime, timedelta, timezone
from threading import Lock

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel

from app.core.auth import require_admin_key
from app.core.feature_flags import hash_actor_token
from app.modules.common.temporal_types import StallLevel
from app.modules.engagement import reminder_engine, unsubscribe_tokens
from app.routes import _appointments_helpers as _h

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/engagement", tags=["engagement"])

_AUTO_DISABLED_CATEGORY = "reminders_auto_disabled"
_UNIFORM_401_DETAIL = "Invalid or expired unsubscribe token."
_RATE_LIMIT_WINDOW = timedelta(hours=1)
_RATE_LIMIT_MAX = 3

# In-process per-actor rate limiter for /send-now. Tests reset via
# the ``_reset_engagement_rate_limit`` autouse fixture.
_RATE_LIMITER: dict[str, list[datetime]] = {}
_RATE_LOCK = Lock()


# -------------------- Helpers --------------------


def _resolve_db_path() -> str:
    """Indirection so tests can monkeypatch the DB path in one place."""
    return _h.resolve_db_path()


def _check_send_now_rate_limit(actor_hash: str) -> bool:
    """True if under the 3-per-hour quota; records the timestamp on success."""
    now = datetime.now(timezone.utc)
    cutoff = now - _RATE_LIMIT_WINDOW
    with _RATE_LOCK:
        history = [ts for ts in _RATE_LIMITER.get(actor_hash, []) if ts > cutoff]
        if len(history) >= _RATE_LIMIT_MAX:
            _RATE_LIMITER[actor_hash] = history
            return False
        history.append(now)
        _RATE_LIMITER[actor_hash] = history
        return True


def _write_auto_disabled(db_path: str, session_id: str) -> None:
    """Persist a single ``reminders_auto_disabled`` row (idempotent-ish)."""
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO engagement_events "
            "(session_id, category, payload_json, created_at) "
            "VALUES (?, ?, ?, ?)",
            (
                session_id, _AUTO_DISABLED_CATEGORY,
                json.dumps({"source": "user_preference"}),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def _clear_auto_disabled(db_path: str, session_id: str) -> None:
    """Remove every opt-out row for a session (re-enable reminders)."""
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "DELETE FROM engagement_events "
            "WHERE session_id = ? AND category = ?",
            (session_id, _AUTO_DISABLED_CATEGORY),
        )
        conn.commit()
    finally:
        conn.close()


def _list_events(db_path: str, session_id: str) -> list[dict]:
    """Return engagement_events rows for ``session_id`` (newest first)."""
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT id, category, payload_json, created_at "
            "FROM engagement_events WHERE session_id = ? "
            "ORDER BY id DESC",
            (session_id,),
        ).fetchall()
    finally:
        conn.close()
    return [
        {
            "id": row[0], "category": row[1],
            "payload": _safe_json(row[2]), "created_at": row[3],
        }
        for row in rows
    ]


def _safe_json(raw: str | None) -> dict:
    """Parse payload_json into a dict (best effort; empty on error)."""
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _dispatch_send_now(session_id: str, db_path: str):
    """Single send-now hook — patched in unit tests to avoid SendGrid.

    Defaults to a SOFT-level reminder so the operator can manually nudge
    a session. The reminder engine handles cooldown + opt-out preflight.
    """
    return reminder_engine.send_reminder(
        session_id, StallLevel.SOFT, db_path=db_path,
    )


# -------------------- Routes --------------------


class PreferencesRequest(BaseModel):
    """Body for ``POST /preferences`` — currently a single boolean."""

    reminders_enabled: bool


class SendNowRequest(BaseModel):
    """Body for ``POST /send-now`` — admin nudges a single session."""

    session_id: str


class UnsubscribeRequest(BaseModel):
    """Body for ``POST /unsubscribe`` — public, signed-token gated."""

    token: str


@router.get("/events")
def list_engagement_events(
    session_id: str = Query(...),
    token: str = Query(...),
) -> dict:
    """Return engagement_events rows owned by ``session_id`` (newest first)."""
    db_path = _resolve_db_path()
    _h.verify_token(db_path, session_id, token)
    return {"events": _list_events(db_path, session_id)}


@router.post("/preferences")
def update_preferences(
    body: PreferencesRequest,
    session_id: str = Query(...),
    token: str = Query(...),
) -> dict:
    """Toggle reminders for a session via the auto-disabled row pattern."""
    db_path = _resolve_db_path()
    _h.verify_token(db_path, session_id, token)
    if body.reminders_enabled:
        _clear_auto_disabled(db_path, session_id)
    else:
        _write_auto_disabled(db_path, session_id)
    return {
        "session_id": session_id,
        "reminders_enabled": body.reminders_enabled,
    }


@router.post("/send-now")
def send_now(
    body: SendNowRequest,
    x_admin_key: str = Header(...),
    _: None = Depends(require_admin_key),
) -> dict:
    """Admin-only manual dispatch — rate-limited 3/hour per admin token."""
    actor_hash = hash_actor_token(x_admin_key)
    if not _check_send_now_rate_limit(actor_hash):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded: max 3 send-now per hour per admin token",
        )
    db_path = _resolve_db_path()
    result = _dispatch_send_now(body.session_id, db_path)
    logger.info(
        "send-now dispatched: session_id=%s success=%s actor_hash=%s",
        body.session_id, result.success, actor_hash[:12],
    )
    return {
        "success": result.success,
        "skipped_reason": result.skipped_reason,
        "category": result.category,
        "message_id": result.message_id,
    }


@router.post("/unsubscribe")
def unsubscribe(body: UnsubscribeRequest) -> dict:
    """Verify a signed unsubscribe token and disable reminders."""
    db_path = _resolve_db_path()
    try:
        session_id = unsubscribe_tokens.verify(body.token, db_path=db_path)
    except unsubscribe_tokens.TokenError:
        logger.debug("unsubscribe-token rejected", exc_info=True)
        raise HTTPException(
            status_code=401, detail=_UNIFORM_401_DETAIL,
        ) from None
    _write_auto_disabled(db_path, session_id)
    return {
        "session_id": session_id,
        "reminders_enabled": False,
    }


__all__ = ["router"]

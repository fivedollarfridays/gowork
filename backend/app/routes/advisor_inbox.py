"""Advisor inbox routes — stalled-session list + detail + note (T12.31).

Three city-scoped endpoints back the case-manager "Needs Attention"
UI. Every handler depends on
:func:`app.core.advisor_auth.require_advisor_token` which returns
``(advisor_id, city)``; the ``city`` threads through the repository
layer (:mod:`app.modules.advisor.repository`) as a mandatory filter.

Contract (see ``docs/security/advisor-auth.md`` section 10):

* C1 — uniform 401 on any auth failure (dependency handles this).
* C2 — repository-layer city filter, not post-filter.
* C3 — cross-city detail access → HTTP **403**, never 404 or empty.
* C4 — every advisor action writes an ``engagement_events`` row with
  ``category='advisor_action'`` and a SHA256-hashed advisor id.
* C5 — 401 body is byte-identical (dependency).
* C6 — per-advisor 3/hour rate limit on the send-note endpoint.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import threading
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from fastapi import Header

from app.core.advisor_auth import (
    hash_advisor_id,
    validate_token,
)
from app.modules.advisor import repository as advisor_repo
from app.modules.engagement import reminder_engine
from app.routes import _appointments_helpers as _db_helpers

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/advisor", tags=["advisor"])

# Per-advisor quota on send-note. Generous for normal advisor workflow;
# clamps spammy / automated note fire-offs. Section 10 C6.
_RATE_LIMIT_MAX = 3
_RATE_LIMIT_WINDOW = timedelta(hours=1)
_RATE_LIMITER: dict[str, list[datetime]] = {}
_RATE_LOCK = threading.Lock()


def _resolve_db_path() -> str:
    """Shared DB-path resolver — monkeypatched by tests."""
    return _db_helpers.resolve_db_path()


def require_advisor_token(
    x_admin_key: str = Header(...),
) -> tuple[str, str]:
    """Route-local wrapper around ``validate_token``.

    Calls the module-local :func:`_resolve_db_path` so tests that
    monkeypatch the router's DB resolver also swap the auth-path DB
    lookup. Uniform 401 body on any failure (missing row, revoked
    row, expired row) per section 10 C5 of the runbook.
    """
    db_path = _resolve_db_path()
    result = validate_token(db_path, x_admin_key)
    if result is None:
        raise HTTPException(
            status_code=401, detail="Invalid advisor token",
        )
    return result


def _enforce_rate_limit(advisor_id: str) -> None:
    """Raise 429 when the advisor has hit the per-hour send-note quota."""
    now = datetime.now(timezone.utc)
    cutoff = now - _RATE_LIMIT_WINDOW
    with _RATE_LOCK:
        history = [
            ts for ts in _RATE_LIMITER.get(advisor_id, []) if ts > cutoff
        ]
        if len(history) >= _RATE_LIMIT_MAX:
            _RATE_LIMITER[advisor_id] = history
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded: 3 advisor notes per hour",
            )
        history.append(now)
        _RATE_LIMITER[advisor_id] = history


def _build_audit_payload(
    *, advisor_id: str, city: str, action: str,
    session_id: str | None, extra: dict[str, Any] | None,
) -> dict[str, Any]:
    """Compose the JSON payload for an advisor-action audit row."""
    payload: dict[str, Any] = {
        "action": action,
        "advisor_id_hash": hash_advisor_id(advisor_id),
        "city": city,
        "session_id": session_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if extra:
        payload.update(extra)
    return payload


def _audit_advisor_action(
    *, db_path: str, advisor_id: str, city: str,
    action: str, session_id: str | None, extra: dict[str, Any] | None = None,
) -> None:
    """Write an ``engagement_events`` row tagging the advisor action.

    Uses the SHA256-hashed advisor id so a compromised audit dump
    cannot reverse-resolve the operator id. Section 10 C4.
    ``engagement_events.session_id`` has a NOT NULL + FK constraint,
    so list-level audits (no session) fall back to a placeholder row
    that is excluded from worker-facing queries by category filter.
    """
    payload = _build_audit_payload(
        advisor_id=advisor_id, city=city, action=action,
        session_id=session_id, extra=extra,
    )
    sid = session_id or "_advisor_audit"
    conn = sqlite3.connect(db_path)
    try:
        if session_id is None:
            _ensure_audit_placeholder_session(conn, sid)
        conn.execute(
            "INSERT INTO engagement_events "
            "(session_id, category, payload_json, created_at) "
            "VALUES (?, 'advisor_action', ?, ?)",
            (
                sid,
                json.dumps(payload, separators=(",", ":"), sort_keys=True),
                payload["timestamp"],
            ),
        )
        conn.commit()
    finally:
        conn.close()


def _ensure_audit_placeholder_session(
    conn: sqlite3.Connection, sid: str,
) -> None:
    """Ensure a no-data placeholder session row exists for list audits.

    Convention: this row uses the literal id ``_advisor_audit`` (single
    placeholder shared across all advisors), is created with
    ``expires_at == created_at`` (already expired, so worker-facing
    queries that filter on expiry skip it), and carries ``demo=1``
    (m005 column) so analytics + advisor-inbox queries that filter
    ``demo = 0`` also skip it. Without ``demo=1`` this row could leak
    into any query that didn't filter on expiry.
    """
    row = conn.execute(
        "SELECT 1 FROM sessions WHERE id = ?", (sid,),
    ).fetchone()
    if row is not None:
        return
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO sessions (id, created_at, barriers, profile, "
        "expires_at, demo) VALUES (?, ?, '[]', '{}', ?, 1)",
        (sid, now, now),
    )


# ------------------------------------------------------------------ schemas


class AdvisorNoteBody(BaseModel):
    """POST body for ``/sessions/{id}/note``."""

    message: str = Field(..., min_length=1, max_length=2000)


# ------------------------------------------------------------------ endpoints


@router.get("/stalled-sessions")
def list_stalled_sessions(
    advisor: tuple[str, str] = Depends(require_advisor_token),
) -> dict:
    """Return stalled sessions for the advisor's city, sorted by severity."""
    advisor_id, city = advisor
    db_path = _resolve_db_path()
    items = advisor_repo.list_stalled_sessions_for_city(db_path, city)
    _audit_advisor_action(
        db_path=db_path, advisor_id=advisor_id, city=city,
        action="list_stalled_sessions", session_id=None,
        extra={"count": len(items)},
    )
    return {
        "sessions": [
            {
                "session_id": s.session_id,
                "city": s.city,
                "stall_level": s.stall_level,
                "days_stalled": s.days_stalled,
            }
            for s in items
        ],
    }


@router.get("/sessions/{session_id}")
def get_session_detail(
    session_id: str,
    advisor: tuple[str, str] = Depends(require_advisor_token),
) -> dict:
    """Return detail for ``session_id``; 403 when the session is in another city."""
    advisor_id, city = advisor
    db_path = _resolve_db_path()
    detail = advisor_repo.get_session_detail_for_city(
        db_path, session_id, city,
    )
    if detail is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if detail.city != city:
        raise HTTPException(
            status_code=403, detail="Cross-city access denied",
        )
    _audit_advisor_action(
        db_path=db_path, advisor_id=advisor_id, city=city,
        action="view_session_detail", session_id=session_id,
    )
    return {
        "session_id": detail.session_id,
        "city": detail.city,
        "stall_level": detail.stall_level,
        "days_stalled": detail.days_stalled,
    }


@router.post("/sessions/{session_id}/note")
def send_note(
    session_id: str,
    body: AdvisorNoteBody,
    advisor: tuple[str, str] = Depends(require_advisor_token),
) -> dict:
    """Send a personal advisor note through the reminder engine."""
    advisor_id, city = advisor
    db_path = _resolve_db_path()
    detail = advisor_repo.get_session_detail_for_city(
        db_path, session_id, city,
    )
    if detail is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if detail.city != city:
        raise HTTPException(
            status_code=403, detail="Cross-city access denied",
        )
    _enforce_rate_limit(advisor_id)
    result = reminder_engine.send_advisor_note(
        session_id, body.message, db_path=db_path,
    )
    _audit_advisor_action(
        db_path=db_path, advisor_id=advisor_id, city=city,
        action="send_note", session_id=session_id,
        extra={
            "success": bool(getattr(result, "success", False)),
            "skipped_reason": getattr(result, "skipped_reason", None),
        },
    )
    return {
        "success": bool(getattr(result, "success", False)),
        "skipped_reason": getattr(result, "skipped_reason", None),
        "message_id": getattr(result, "message_id", None),
    }


__all__ = ["router"]

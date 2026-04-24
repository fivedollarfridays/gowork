"""Nightly-status helper for :mod:`reminder_engine` (T12.25b).

Extracted so the engine stays under the 300-line / 15-function arch
budget. Side-effect free: reads ``engagement_events`` only. Exposed to
the engine as :func:`reminder_engine.nightly_status` via a bare import.

Health rules:

* ``healthy`` — a ``digest_sent`` event landed within the freshness
  window (2 days).
* ``degraded`` — ``reminders_auto_disabled`` is set, OR events exist
  but no recent digest (stale).
* ``unknown`` — no engagement_events rows for this session.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.modules.common.temporal_types import ModuleStatus

_DIGEST_FRESH_DAYS = 2


def nightly_status(
    session_id: str, *, db_path: str | Path, now: datetime | None = None,
) -> ModuleStatus:
    """Report engagement-engine health for ``session_id``."""
    reference = now or datetime.now(timezone.utc)
    counts = _read_counts(session_id, db_path=db_path)
    health = _classify(counts=counts, now=reference)
    signals: dict[str, Any] = {
        "digest_sent_count": counts["digest_sent_count"],
        "reminder_sent_count": counts["reminder_sent_count"],
        "reminders_auto_disabled": counts["reminders_auto_disabled"],
    }
    return ModuleStatus(
        module_name="reminder_engine",
        health=health, signals=signals,
        last_activity_at=counts["last_at"],
    )


def _read_counts(session_id: str, *, db_path: str | Path) -> dict[str, Any]:
    """Aggregate engagement_events counts + last activity for the session."""
    conn = sqlite3.connect(str(db_path))
    try:
        row = conn.execute(
            "SELECT "
            "  SUM(CASE WHEN category = 'digest_sent' THEN 1 ELSE 0 END), "
            "  SUM(CASE WHEN category = 'reminder_sent' THEN 1 ELSE 0 END), "
            "  SUM(CASE WHEN category = 'reminders_auto_disabled' "
            "           THEN 1 ELSE 0 END), "
            "  MAX(created_at) "
            "FROM engagement_events WHERE session_id = ?",
            (session_id,),
        ).fetchone()
    finally:
        conn.close()
    digest = int(row[0] or 0) if row else 0
    reminder = int(row[1] or 0) if row else 0
    disabled = bool(int(row[2] or 0)) if row else False
    last_raw = row[3] if row else None
    return {
        "digest_sent_count": digest,
        "reminder_sent_count": reminder,
        "reminders_auto_disabled": disabled,
        "last_at": _parse_iso(last_raw) if last_raw else None,
    }


def _parse_iso(value: str) -> datetime | None:
    try:
        dt = datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _classify(*, counts: dict[str, Any], now: datetime) -> str:
    if counts["reminders_auto_disabled"]:
        return "degraded"
    last_at: datetime | None = counts["last_at"]
    if last_at is None:
        return "unknown"
    if counts["digest_sent_count"] > 0 and (now - last_at).days <= _DIGEST_FRESH_DAYS:
        return "healthy"
    return "degraded"


__all__ = ["nightly_status"]

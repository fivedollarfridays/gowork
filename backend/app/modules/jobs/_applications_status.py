"""Nightly-status helper for :mod:`applications` (T12.25b).

Extracted so the applications CRUD module stays under the 150-line
warning threshold. Side-effect free: reads ``job_applications`` only.
Exposed as :func:`applications.nightly_status` via a bare import.

Health rules:

* ``healthy`` — any activity within the freshness window (7 days).
* ``degraded`` — ≥ 3 pending applications (draft/applied/interview)
  AND no activity in the last 7 days — a stuck pipeline.
* ``unknown`` — no applications for this session.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.modules.common.temporal_types import ModuleStatus

_STALE_DAYS = 7
_PENDING_STATUSES = ("draft", "applied", "interview")


def nightly_status(
    session_id: str, *, db_path: str | Path, now: datetime | None = None,
) -> ModuleStatus:
    """Report job-application pipeline health for ``session_id``."""
    reference = now or datetime.now(timezone.utc)
    total, pending, last_at = _read_pipeline(session_id, db_path=db_path)
    health = _classify(
        total=total, pending=pending, last_at=last_at, now=reference,
    )
    signals: dict[str, Any] = {"total": total, "pending": pending}
    return ModuleStatus(
        module_name="applications",
        health=health, signals=signals, last_activity_at=last_at,
    )


def _read_pipeline(
    session_id: str, *, db_path: str | Path,
) -> tuple[int, int, datetime | None]:
    """Return ``(total, pending, last_created_at)`` for one session."""
    placeholders = ",".join("?" * len(_PENDING_STATUSES))
    conn = sqlite3.connect(str(db_path))
    try:
        total_row = conn.execute(
            "SELECT COUNT(*), MAX(created_at) FROM job_applications "
            "WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        pending_row = conn.execute(
            f"SELECT COUNT(*) FROM job_applications "
            f"WHERE session_id = ? AND status IN ({placeholders})",
            (session_id, *_PENDING_STATUSES),
        ).fetchone()
    finally:
        conn.close()
    total = int(total_row[0]) if total_row and total_row[0] is not None else 0
    pending = int(pending_row[0]) if pending_row and pending_row[0] is not None else 0
    last_raw = total_row[1] if total_row else None
    last_at = _parse_iso(last_raw) if last_raw else None
    return total, pending, last_at


def _parse_iso(value: str) -> datetime | None:
    try:
        dt = datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _classify(
    *, total: int, pending: int, last_at: datetime | None, now: datetime,
) -> str:
    if total == 0 or last_at is None:
        return "unknown"
    if (now - last_at).days > _STALE_DAYS and pending >= 3:
        return "degraded"
    return "healthy"


__all__ = ["nightly_status"]

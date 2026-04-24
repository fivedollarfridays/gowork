"""DB + trigger helpers for plan_refresher (T12.24, S12b).

Split out of ``plan_refresher`` to keep the hub module under the
project's per-file limits (15 functions / 20 imports / 400 lines).
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from app.modules.common.temporal_types import StallLevel
from app.modules.engagement.stall_detector import compute_stall_for_session

# Window within which a barrier_resolved outcome counts as a "breakthrough"
# worthy of an immediate plan refresh. Narrow window keeps the refresher
# from re-triggering on the same event across successive nightly runs.
BREAKTHROUGH_WINDOW = timedelta(hours=24)

# Application-level cap on plan_history rows per session. The m002 migration
# documents this as "enforced in T12.24 (application code; NOT at schema
# level)" — see the inline comment in m002_s12_worker_companion.py.
PLAN_HISTORY_CAP_PER_SESSION = 20


def load_session_row(session_id: str, db_path: str | Path) -> dict | None:
    """Return the needed session columns as a dict, or None if missing."""
    conn = sqlite3.connect(str(db_path))
    try:
        row = conn.execute(
            "SELECT barriers, plan, benefits_profile, action_checklist "
            "FROM sessions WHERE id = ?",
            (session_id,),
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        return None
    return {
        "barriers": _parse_json(row[0]) or [],
        "plan": _parse_json(row[1]) or {},
        "benefits_profile": _parse_json(row[2]) or {},
        "action_checklist": _parse_json(row[3]) or {},
    }


def _parse_json(raw: str | None) -> Any:
    """Parse a JSON column safely; return None on failure."""
    if not raw:
        return None
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None


def detect_breakthrough(
    session_id: str, *, db_path: str | Path, now: datetime,
) -> str | None:
    """Return a descriptive event string if a recent breakthrough exists."""
    cutoff = (now - BREAKTHROUGH_WINDOW).isoformat()
    conn = sqlite3.connect(str(db_path))
    try:
        row = conn.execute(
            "SELECT payload_json, created_at FROM outcomes_records "
            "WHERE session_id = ? AND event_type = 'barrier_resolved' "
            "AND created_at >= ? "
            "ORDER BY created_at DESC LIMIT 1",
            (session_id, cutoff),
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        return None
    payload = _parse_json(row[0]) or {}
    barrier = payload.get("barrier_id") if isinstance(payload, dict) else None
    return f"barrier_resolved:{barrier or 'unknown'}"


def detect_stall_hard(
    session_id: str,
    *,
    db_path: str | Path,
    now: datetime,
    compute_fn=compute_stall_for_session,
) -> str | None:
    """Return a descriptive event string if the session is HARD-stalled."""
    stalled = compute_fn(session_id, db_path=db_path, now=now)
    if stalled.stall_level is not StallLevel.HARD:
        return None
    return f"stall_level=hard;days={stalled.days_stalled}"


def archive_plan(
    session_id: str,
    old_plan: dict,
    *,
    db_path: str | Path,
    archived_at: datetime,
    refresh_reason: str,
    triggering_event: str | None,
) -> None:
    """Insert one plan_history row and evict older rows above the cap.

    Dual-write to ``sessions.previous_plan`` is the caller's job (kept
    in the orchestrator so the write and the cap enforcement stay
    visually paired).
    """
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute(
            "INSERT INTO plan_history "
            "(session_id, archived_at, plan_json, refresh_reason, triggering_event) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                session_id,
                archived_at.isoformat(),
                json.dumps(old_plan),
                refresh_reason,
                triggering_event,
            ),
        )
        _enforce_history_cap(conn, session_id)
        conn.commit()
    finally:
        conn.close()


def _enforce_history_cap(conn: sqlite3.Connection, session_id: str) -> None:
    """Delete rows for ``session_id`` beyond the newest PLAN_HISTORY_CAP_PER_SESSION."""
    conn.execute(
        "DELETE FROM plan_history WHERE session_id = ? AND id NOT IN ("
        "SELECT id FROM plan_history WHERE session_id = ? "
        "ORDER BY archived_at DESC, id DESC LIMIT ?"
        ")",
        (session_id, session_id, PLAN_HISTORY_CAP_PER_SESSION),
    )


def write_new_plan(
    session_id: str,
    *,
    db_path: str | Path,
    old_plan: dict,
    new_plan: dict,
    new_checklist: dict,
) -> None:
    """Persist the new plan + carry-forward checklist + dual-writes previous_plan.

    Dual-write target (``sessions.previous_plan``) is deprecated in S13;
    the ``plan_history`` row is the canonical store going forward.
    """
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute(
            "UPDATE sessions SET plan = ?, previous_plan = ?, action_checklist = ? "
            "WHERE id = ?",
            (
                json.dumps(new_plan),
                json.dumps(old_plan),
                json.dumps(new_checklist),
                session_id,
            ),
        )
        conn.commit()
    finally:
        conn.close()


__all__ = [
    "BREAKTHROUGH_WINDOW",
    "PLAN_HISTORY_CAP_PER_SESSION",
    "archive_plan",
    "detect_breakthrough",
    "detect_stall_hard",
    "load_session_row",
    "write_new_plan",
]

"""Bridge job_application events → append-only outcomes_records (T12.11).

Mirrors `app.modules.appointments.outcomes_listener`. Coupling is via
the in-process event bus (`app.core.events`); job lifecycle writers never
import this module. At startup, `main.py` calls
`register_jobs_outcomes_listener(db_path)` which wires handlers for every
lifecycle event.

Event → signal_type mapping:
    job_application.created    → "job_application_created"
    job_application.applied    → "job_application_applied"
    job_application.interview  → "job_application_interview"
    job_application.offer      → "job_application_offer"
    job_application.rejected   → "job_application_rejected"
    job_application.withdrawn  → "job_application_withdrawn"

cleared_barriers snapshot
-------------------------
Each outcome row stores a snapshot pulled from the session's profile
JSON. If the session's profile has a `cleared_barriers` field, it is
preserved in `barriers_cleared_snapshot_json`; otherwise an empty list
is recorded. This feeds the N+1 intelligence calibration (T12.12+).
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from app.core import events
from app.modules.outcomes.tracker_sql import connect, now_iso

_SIGNAL_BY_EVENT: dict[str, str] = {
    "job_application.created": "job_application_created",
    "job_application.applied": "job_application_applied",
    "job_application.interview": "job_application_interview",
    "job_application.offer": "job_application_offer",
    "job_application.rejected": "job_application_rejected",
    "job_application.withdrawn": "job_application_withdrawn",
}

_INSERT_SQL = (
    "INSERT INTO outcomes_records "
    "(session_id, event_type, payload_json, created_at, "
    "barriers_cleared_snapshot_json) "
    "VALUES (?, ?, ?, ?, ?)"
)


def _load_cleared_barriers(
    session_id: str, conn: sqlite3.Connection,
) -> list[str]:
    """Return the session's `cleared_barriers` list from its profile JSON.

    Returns an empty list when the session is missing, has no profile,
    or the profile doesn't carry a `cleared_barriers` field. Silent on
    JSON parse failures — snapshot is best-effort.
    """
    row = conn.execute(
        "SELECT profile FROM sessions WHERE id = ?", (session_id,),
    ).fetchone()
    if not row or not row[0]:
        return []
    try:
        profile = json.loads(row[0])
    except (json.JSONDecodeError, TypeError):
        return []
    if not isinstance(profile, dict):
        return []
    cleared = profile.get("cleared_barriers") or []
    return list(cleared) if isinstance(cleared, list) else []


def _build_payload(payload: dict, signal_type: str) -> str:
    """Minimal payload JSON for job lifecycle rows."""
    return json.dumps({
        "signal_type": signal_type,
        "application_id": payload.get("id"),
        "status": payload.get("status"),
        "match_source": payload.get("match_source"),
        "match_url": payload.get("match_url"),
        "company": payload.get("company"),
        "role": payload.get("role"),
    })


def _write_outcome(
    db_path: str | Path,
    session_id: str,
    signal_type: str,
    payload: dict,
) -> None:
    """Append an outcomes_records row for the job event."""
    conn = connect(db_path)
    try:
        cleared = _load_cleared_barriers(session_id, conn)
        snapshot = json.dumps({"cleared_barriers": cleared})
        conn.execute(
            _INSERT_SQL,
            (
                session_id,
                signal_type,
                _build_payload(payload, signal_type),
                now_iso(),
                snapshot,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def _make_handler(signal_type: str, db_path: str | Path):
    """Return a handler bound to `signal_type` and the tracker's db_path."""

    def _handle(payload: dict) -> None:
        session_id = payload.get("session_id")
        if not session_id:
            return
        _write_outcome(db_path, session_id, signal_type, payload)

    return _handle


def register_jobs_outcomes_listener(db_path: str | Path) -> None:
    """Subscribe outcome handlers to every mapped job_application event.

    Idempotent at the bus level — duplicate `subscribe()` is a no-op —
    but each call here creates *new* handler closures. Call once at
    startup. Tests that re-register should first call
    `events.clear_all_subscribers()`.
    """
    for event_name, signal_type in _SIGNAL_BY_EVENT.items():
        events.subscribe(event_name, _make_handler(signal_type, db_path))


__all__ = ["register_jobs_outcomes_listener"]

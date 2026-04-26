"""Worker-companion demo seed data (S12b T12.34, S13 T13.2).

Hub that orchestrates the worker-companion demo seed: 5 sessions per
city × 2 cities = 10 sessions covering all stall states (none / soft /
medium / hard / breakthrough). Per-row insert helpers live in
:mod:`app._demo_seed_rows`; QC-state extension layered by T13.2 (compliance
+ weekly review + advisor inbox + reminder state) lives in
:mod:`app._demo_seed_qc`.

Design
------
- Plain sqlite3 (no SQLAlchemy) — matches T12.18 stall_detector and
  T12.12 funnel_queries so seeded rows round-trip through the same code
  paths.
- Deterministic: session ids are SHA256-derived UUIDs so idempotent
  re-runs hash to the same id (PK collision → INSERT OR IGNORE).
- ``sessions.profile`` carries ``{"city": <city>, "demo_stall_state":
  <state>}`` for test visibility. The canonical city tag for T12.12 is
  written into ``outcomes_records.payload_json.city``.
- Stall is steered by planting a single progress event at the right age:
  none → 1d, soft → 4d, medium → 10d, hard → 18d, breakthrough → 20d
  baseline + a fresh barrier_resolved within the 24h BREAKTHROUGH window.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app._demo_seed_qc import seed_qc_state
from app._demo_seed_rows import (
    STATE_BARRIER,
    STATE_PROGRESS_AGE_DAYS,
    insert_application,
    insert_appointment,
    insert_outcomes_rows,
    insert_resume_version,
    insert_snapshot,
)

CITIES: tuple[str, ...] = ("montgomery", "fort-worth")
STATES: tuple[str, ...] = ("none", "soft", "medium", "hard", "breakthrough")


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def _session_id(city: str, state: str) -> str:
    """Deterministic UUID per (city, state).

    OutcomeRecord validates this as a UUID-shape string, so an ad-hoc
    ``demo-...`` id would be rejected by the outcomes tracker downstream.
    We seed a v4 UUID out of a sha256 of the label so idempotent re-runs
    still hash to the same id.
    """
    digest = hashlib.sha256(f"s12b-demo:{city}:{state}".encode()).digest()
    return str(uuid.UUID(bytes=digest[:16], version=4))


def _session_profile(city: str, state: str) -> str:
    return json.dumps({
        "city": city,
        "demo_stall_state": state,
        "primary_barrier": STATE_BARRIER[state],
        "seed_source": "s12b_worker_companion",
    })


def _insert_session(
    conn: sqlite3.Connection, city: str, state: str, now: datetime,
) -> str:
    """Insert one demo session row; idempotent via INSERT OR IGNORE."""
    sid = _session_id(city, state)
    expires = _iso(now + timedelta(days=90))
    barriers_json = json.dumps([STATE_BARRIER[state]])
    conn.execute(
        "INSERT OR IGNORE INTO sessions "
        "(id, created_at, barriers, profile, expires_at, demo) "
        "VALUES (?, ?, ?, ?, ?, 1)",
        (sid, _iso(now - timedelta(days=30)), barriers_json,
         _session_profile(city, state), expires),
    )
    return sid


def _seed_one(
    conn: sqlite3.Connection, city: str, state: str, now: datetime,
) -> str:
    """Seed one session and all of its support rows.

    Idempotency is split between two layers:

    1. The base support rows (appointment / application / resume /
       snapshot / outcomes) are skipped wholesale when an appointment
       already exists for the session — preserves the original T12.34
       behaviour.
    2. The T13.2 QC state spoke is invoked unconditionally; every helper
       inside that spoke is itself idempotent so re-runs are no-ops.
    """
    sid = _insert_session(conn, city, state, now)
    existing = conn.execute(
        "SELECT 1 FROM appointments WHERE session_id = ? LIMIT 1", (sid,),
    ).fetchone()
    if existing is None:
        insert_appointment(conn, sid, state, now)
        insert_application(conn, sid, state, now)
        insert_resume_version(conn, sid, state, now)
        insert_snapshot(conn, sid, state, now)
        insert_outcomes_rows(conn, sid, city, state, now)
    _seed_qc_state_if_schema_ready(conn, sid, city=city, state=state, now=now)
    return sid


def _seed_qc_state_if_schema_ready(
    conn: sqlite3.Connection, sid: str, *,
    city: str, state: str, now: datetime,
) -> None:
    """Invoke the QC seed spoke only when m006 + m007 tables exist.

    The base S12b seed must keep working on DBs that only carry m001 +
    m002 + m005; the QC tables land in m006 + m007. A missing-table
    fallback lets older callers keep their existing behaviour without
    re-applying migrations.
    """
    if not _has_table(conn, "compliance_audit"):
        return
    if not _has_table(conn, "advisor_tokens"):
        return
    seed_qc_state(conn, sid, city=city, state_label=state, now=now)


def _has_table(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name = ?",
        (table,),
    ).fetchone()
    return row is not None


def seed_worker_companion_sessions(
    *, db_path: str | Path, now: datetime | None = None,
) -> dict:
    """Seed 5 × 2 demo sessions spanning all stall states and both cities.

    Returns a summary dict with ``sessions_created`` and ``cities``.
    Idempotent: repeated runs do not duplicate rows.
    """
    now = now or datetime.now(timezone.utc)
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        for city in CITIES:
            for state in STATES:
                _seed_one(conn, city, state, now)
        conn.commit()
    finally:
        conn.close()
    return {
        "sessions_created": len(CITIES) * len(STATES),
        "cities": list(CITIES),
        "states": list(STATES),
    }


__all__ = ["CITIES", "STATES", "seed_worker_companion_sessions"]

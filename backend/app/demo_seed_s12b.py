"""Worker-companion demo seed data (S12b T12.34).

Extends `app.demo_seed` with 5 sessions per city (montgomery + fort-worth)
spanning the 5 stall states (`none`/`soft`/`medium`/`hard`/`breakthrough`).
Every seeded session is marked `demo=1` on `sessions.demo` (added by m005),
so T12.12's community-funnel guard, advisor inboxes, and other intelligence
aggregates exclude them.

Design
------
- Plain sqlite3 (no SQLAlchemy) — matches T12.18 stall_detector and T12.12
  funnel_queries so the seeded rows round-trip through the same code paths.
- Deterministic: session ids are built from `f"demo-s12b-{city}-{state}"`,
  enabling idempotent re-runs (PK-collision → INSERT OR IGNORE).
- `sessions.profile` carries `{"city": <city>, "demo_stall_state": <state>}`
  for test visibility; the canonical city tag for T12.12 is still written
  into `outcomes_records.payload_json.city`.
- Stall is steered by planting a single ``outcomes_records`` progress event
  at the right age:
    * `none` → 1 day ago (below SOFT_DAYS=3)
    * `soft` → 4 days ago (SOFT_DAYS ≤ age < MEDIUM_DAYS=7)
    * `medium` → 10 days ago (MEDIUM_DAYS ≤ age < HARD_DAYS=14)
    * `hard` → 18 days ago (age ≥ HARD_DAYS)
    * `breakthrough` → 20 days old baseline (HARD) + fresh
      `event_type='barrier_resolved'` outcome inside the 24h
      BREAKTHROUGH_WINDOW, so `detect_breakthrough` wins the plan-refresher
      trigger arbitration.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

CITIES: tuple[str, ...] = ("montgomery", "fort-worth")
STATES: tuple[str, ...] = ("none", "soft", "medium", "hard", "breakthrough")

# Age (in days) of the primary progress event per state. Must align with
# `engagement.classification` thresholds (SOFT_DAYS=3 / MEDIUM_DAYS=7 /
# HARD_DAYS=14). Breakthrough uses a HARD-age baseline plus a fresh
# barrier_resolved outcome added on top.
_STATE_PROGRESS_AGE_DAYS: dict[str, int] = {
    "none": 1,
    "soft": 4,
    "medium": 10,
    "hard": 18,
    "breakthrough": 20,
}

# Primary barrier per state (used by appointment.barrier_link + application.role)
_STATE_BARRIER: dict[str, str] = {
    "none": "transportation",
    "soft": "credit",
    "medium": "criminal_record",
    "hard": "childcare",
    "breakthrough": "housing",
}


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def _session_id(city: str, state: str) -> str:
    """Deterministic UUID per (city, state). OutcomeRecord validates this
    as a UUID-shape string, so an ad-hoc `demo-...` id would be rejected
    by the outcomes tracker downstream. We seed a version-4 UUID out of a
    sha256 of the label so idempotent re-runs still hash to the same id.
    """
    digest = hashlib.sha256(f"s12b-demo:{city}:{state}".encode()).digest()
    return str(uuid.UUID(bytes=digest[:16], version=4))


def _session_profile(city: str, state: str) -> str:
    return json.dumps({
        "city": city,
        "demo_stall_state": state,
        "primary_barrier": _STATE_BARRIER[state],
        "seed_source": "s12b_worker_companion",
    })


def _insert_session(conn: sqlite3.Connection, city: str, state: str, now: datetime) -> str:
    """Insert one demo session row; idempotent via INSERT OR IGNORE."""
    sid = _session_id(city, state)
    expires = _iso(now + timedelta(days=90))
    barriers_json = json.dumps([_STATE_BARRIER[state]])
    conn.execute(
        "INSERT OR IGNORE INTO sessions "
        "(id, created_at, barriers, profile, expires_at, demo) "
        "VALUES (?, ?, ?, ?, ?, 1)",
        (sid, _iso(now - timedelta(days=30)), barriers_json,
         _session_profile(city, state), expires),
    )
    return sid


def _insert_outcomes_rows(
    conn: sqlite3.Connection, sid: str, city: str, state: str, now: datetime,
) -> None:
    """Insert outcomes_records: city tag + a progress event at state-age.

    For `breakthrough`, add an additional `barrier_resolved` event within
    the 24h `BREAKTHROUGH_WINDOW` so `_plan_refresher_db.detect_breakthrough`
    returns a non-None reason.
    """
    age_days = _STATE_PROGRESS_AGE_DAYS[state]
    event_at = now - timedelta(days=age_days)
    _insert_outcome(
        conn, sid, "application_filed", now=event_at, city=city,
    )
    if state == "breakthrough":
        fresh = now - timedelta(hours=2)
        _insert_outcome(
            conn, sid, "barrier_resolved", now=fresh, city=city,
            extra={"barrier_id": _STATE_BARRIER[state]},
        )


def _insert_outcome(
    conn: sqlite3.Connection,
    sid: str,
    event_type: str,
    *,
    now: datetime,
    city: str,
    extra: dict | None = None,
) -> None:
    payload: dict = {"city": city}
    if extra:
        payload.update(extra)
    conn.execute(
        "INSERT INTO outcomes_records "
        "(session_id, event_type, payload_json, created_at) "
        "VALUES (?, ?, ?, ?)",
        (sid, event_type, json.dumps(payload), _iso(now)),
    )


def _insert_appointment(
    conn: sqlite3.Connection, sid: str, state: str, now: datetime,
) -> None:
    age_days = _STATE_PROGRESS_AGE_DAYS[state]
    starts = now - timedelta(days=age_days)
    ends = starts + timedelta(hours=1)
    conn.execute(
        "INSERT INTO appointments "
        "(session_id, type, title, starts_at, ends_at, location_name, "
        "location_address, barrier_link, status, source, notes, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            sid,
            "career_center",
            f"Demo {state} — intake appointment",
            _iso(starts),
            _iso(ends),
            "Career Center",
            "123 Main St",
            _STATE_BARRIER[state],
            "attended",
            "user",
            "Seeded by demo_seed_s12b",
            _iso(starts),
        ),
    )


def _insert_application(
    conn: sqlite3.Connection, sid: str, state: str, now: datetime,
) -> None:
    age_days = _STATE_PROGRESS_AGE_DAYS[state]
    applied = (now - timedelta(days=age_days)).date().isoformat()
    conn.execute(
        "INSERT INTO job_applications "
        "(session_id, match_source, match_url, company, role, "
        "resume_version_id, status, applied_date, created_at) "
        "VALUES (?, ?, ?, ?, ?, NULL, ?, ?, ?)",
        (
            sid,
            "twc",
            "https://example.invalid/job",
            f"Demo Employer ({state})",
            "Warehouse Associate",
            "applied",
            applied,
            _iso(now - timedelta(days=age_days)),
        ),
    )


def _insert_resume_version(
    conn: sqlite3.Connection, sid: str, state: str, now: datetime,
) -> None:
    conn.execute(
        "INSERT INTO resume_versions "
        "(session_id, doc_type, version_counter, markdown, target_job_source, "
        "target_job_url, barriers_framed_json, generation_method, "
        "use_counter, created_at) "
        "VALUES (?, 'resume', 1, ?, 'twc', "
        "'https://example.invalid/job', '[]', 'template', 0, ?)",
        (
            sid,
            f"# Demo resume for {sid}\n\nSeeded by demo_seed_s12b ({state}).",
            _iso(now - timedelta(days=30)),
        ),
    )


def _insert_snapshot(
    conn: sqlite3.Connection, sid: str, state: str, now: datetime,
) -> None:
    snap_date = (now - timedelta(days=1)).date().isoformat()
    conn.execute(
        "INSERT INTO daily_progress_snapshots "
        "(session_id, date, expected_actions_json, evidence_json, "
        "classifications_json, created_at) "
        "VALUES (?, ?, '[]', '{}', ?, ?)",
        (
            sid, snap_date,
            json.dumps({"demo_stall_state": state}),
            _iso(now - timedelta(days=1)),
        ),
    )


def _seed_one(
    conn: sqlite3.Connection, city: str, state: str, now: datetime,
) -> str:
    """Seed one session plus its appointment/application/resume/snapshot/outcomes."""
    sid = _insert_session(conn, city, state, now)
    # Idempotency guard: skip support rows if already seeded.
    existing = conn.execute(
        "SELECT 1 FROM appointments WHERE session_id = ? LIMIT 1", (sid,),
    ).fetchone()
    if existing is not None:
        return sid
    _insert_appointment(conn, sid, state, now)
    _insert_application(conn, sid, state, now)
    _insert_resume_version(conn, sid, state, now)
    _insert_snapshot(conn, sid, state, now)
    _insert_outcomes_rows(conn, sid, city, state, now)
    return sid


def seed_worker_companion_sessions(
    *, db_path: str | Path, now: datetime | None = None,
) -> dict:
    """Seed 5 × 2 demo sessions spanning all stall states and both cities.

    Returns a summary dict with `sessions_created` and `cities`.
    Idempotent: repeated runs do not duplicate rows (PK-collision on
    sessions + pre-check on appointments).
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

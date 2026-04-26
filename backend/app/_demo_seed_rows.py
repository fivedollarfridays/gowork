"""Per-row insert helpers for the worker-companion seed (T12.34, T13.2).

Extracted from :mod:`app.demo_seed_s12b` so the hub stays under the
project arch ceiling (300 lines / 12 functions). One helper per
support table: appointment, application, resume + cover-letter,
snapshot, outcomes. Each is idempotent in the sense that the hub's
``_seed_one`` only invokes them once per (city, state) tuple.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta


__all__ = [
    "STATE_PROGRESS_AGE_DAYS",
    "STATE_BARRIER",
    "insert_appointment",
    "insert_application",
    "insert_resume_version",
    "insert_snapshot",
    "insert_outcomes_rows",
]


STATE_PROGRESS_AGE_DAYS: dict[str, int] = {
    "none": 1,
    "soft": 4,
    "medium": 10,
    "hard": 18,
    "breakthrough": 20,
}


STATE_BARRIER: dict[str, str] = {
    "none": "transportation",
    "soft": "credit",
    "medium": "criminal_record",
    "hard": "childcare",
    "breakthrough": "housing",
}


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def insert_appointment(
    conn: sqlite3.Connection, sid: str, state: str, now: datetime,
) -> None:
    """Plant one ``appointments`` row for the seeded session."""
    age_days = STATE_PROGRESS_AGE_DAYS[state]
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
            _iso(starts), _iso(ends),
            "Career Center", "123 Main St",
            STATE_BARRIER[state],
            "attended", "user",
            "Seeded by demo_seed_s12b",
            _iso(starts),
        ),
    )


def insert_application(
    conn: sqlite3.Connection, sid: str, state: str, now: datetime,
) -> None:
    """Plant one ``job_applications`` row at the per-state age."""
    age_days = STATE_PROGRESS_AGE_DAYS[state]
    applied = (now - timedelta(days=age_days)).date().isoformat()
    conn.execute(
        "INSERT INTO job_applications "
        "(session_id, match_source, match_url, company, role, "
        "resume_version_id, status, applied_date, created_at) "
        "VALUES (?, ?, ?, ?, ?, NULL, ?, ?, ?)",
        (
            sid, "twc", "https://example.invalid/job",
            f"Demo Employer ({state})", "Warehouse Associate",
            "applied", applied,
            _iso(now - timedelta(days=age_days)),
        ),
    )


def insert_resume_version(
    conn: sqlite3.Connection, sid: str, state: str, now: datetime,
) -> None:
    """Plant a resume row plus a matching cover_letter row.

    The cover_letter row gives the cover_letter_builder module a
    non-``unknown`` ``nightly_status`` for the T13.2 QC coverage
    assertion. Both rows share ``version_counter=1`` because the
    monotonic counter is per-(session, doc_type).
    """
    _insert_doc(
        conn, sid, doc_type="resume",
        body=f"# Demo resume for {sid}\n\nSeeded by demo_seed_s12b ({state}).",
        created_at=_iso(now - timedelta(days=30)),
    )
    _insert_doc(
        conn, sid, doc_type="cover_letter",
        body=f"Dear hiring team,\n\nDemo cover letter for {sid} ({state}).",
        created_at=_iso(now - timedelta(days=2)),
    )


def _insert_doc(
    conn: sqlite3.Connection, sid: str,
    *, doc_type: str, body: str, created_at: str,
) -> None:
    conn.execute(
        "INSERT INTO resume_versions "
        "(session_id, doc_type, version_counter, markdown, target_job_source, "
        "target_job_url, barriers_framed_json, generation_method, "
        "use_counter, created_at) "
        "VALUES (?, ?, 1, ?, 'twc', 'https://example.invalid/job', "
        "'[]', 'template', 0, ?)",
        (sid, doc_type, body, created_at),
    )


def insert_snapshot(
    conn: sqlite3.Connection, sid: str, state: str, now: datetime,
) -> None:
    """Plant one ``daily_progress_snapshots`` row tagged with the state."""
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


def insert_outcomes_rows(
    conn: sqlite3.Connection, sid: str, city: str, state: str, now: datetime,
) -> None:
    """Plant outcomes_records: city tag + a progress event at state-age.

    For ``breakthrough``, add a ``barrier_resolved`` event within the 24h
    BREAKTHROUGH_WINDOW so ``detect_breakthrough`` returns non-None.
    """
    age_days = STATE_PROGRESS_AGE_DAYS[state]
    event_at = now - timedelta(days=age_days)
    _insert_outcome(conn, sid, "application_filed", now=event_at, city=city)
    if state == "breakthrough":
        fresh = now - timedelta(hours=2)
        _insert_outcome(
            conn, sid, "barrier_resolved", now=fresh, city=city,
            extra={"barrier_id": STATE_BARRIER[state]},
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

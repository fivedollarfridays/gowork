"""Data-collection helpers for the digest composer (T12.20).

Extracted from ``digest_composer`` so that module stays under the 300-
line architecture ceiling. Owns the DB-facing reads: worker first name
from ``sessions.profile``, yesterday's cleared-barrier scan, and the
today/this-week appointment filters.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from app.modules.appointments import scheduler
from app.modules.appointments.types import Appointment
from app.modules.plan.evidence_collector import EvidenceBundle, collect_evidence


def resolve_first_name(db_path: str | Path, session_id: str) -> str:
    """Resolve worker first name via ``profile.first_name`` -> ``name`` -> fallback."""
    conn = sqlite3.connect(str(db_path))
    try:
        row = conn.execute(
            "SELECT profile FROM sessions WHERE id = ?", (session_id,),
        ).fetchone()
    finally:
        conn.close()
    if not row or not row[0]:
        return "friend"
    try:
        profile = json.loads(row[0])
    except (json.JSONDecodeError, TypeError):
        return "friend"
    if not isinstance(profile, dict):
        return "friend"
    first = profile.get("first_name")
    if isinstance(first, str) and first.strip():
        return first.strip()
    name = profile.get("name")
    if isinstance(name, str) and name.strip():
        return name.strip().split()[0]
    return "friend"


def collect_yesterday(
    session_id: str, for_date: date, db_path: str | Path,
) -> tuple[EvidenceBundle, list[str]]:
    """Return (evidence bundle for yesterday, list of cleared-barrier ids)."""
    yesterday = for_date - timedelta(days=1)
    bundle = collect_evidence(
        session_id, start=yesterday, end=yesterday, db_path=db_path,
    )
    cleared = _barriers_cleared_on(session_id, yesterday, db_path)
    return bundle, cleared


def _barriers_cleared_on(
    session_id: str, day: date, db_path: str | Path,
) -> list[str]:
    """Return barrier ids from outcomes_records whose event_type is a clear/resolve.

    Scans by ``created_at`` date prefix since outcomes store ISO-8601
    UTC strings. Accepts both ``barrier.cleared`` (spec-preferred) and
    ``barrier_resolved`` (already written by outcomes listeners).
    """
    iso = day.isoformat()
    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute(
            "SELECT payload_json FROM outcomes_records "
            "WHERE session_id = ? AND substr(created_at, 1, 10) = ? "
            "AND (event_type = 'barrier.cleared' "
            "     OR event_type = 'barrier_resolved')",
            (session_id, iso),
        ).fetchall()
    finally:
        conn.close()
    names: list[str] = []
    for (payload,) in rows:
        try:
            data = json.loads(payload) if payload else {}
        except (json.JSONDecodeError, TypeError):
            data = {}
        barrier = data.get("barrier_id") if isinstance(data, dict) else None
        if isinstance(barrier, str) and barrier.strip():
            names.append(barrier.strip())
    return names


def collect_today(
    session_id: str,
    for_date: date,
    db_path: str | Path,
    now: datetime,
) -> tuple[list[Appointment], list[Appointment]]:
    """Return (today_scheduled_future, yesterday_missed).

    Only ``SCHEDULED`` appointments surface in "today" — missed items
    flow to the carryover subsection.
    """
    rows = scheduler.list_by_session(session_id, db_path=db_path)
    today_items = [
        a for a in rows
        if a.status.value == "scheduled"
        and a.starts_at is not None
        and a.starts_at.astimezone(timezone.utc).date() == for_date
        and a.starts_at >= now
    ]
    yesterday = for_date - timedelta(days=1)
    yesterday_missed = [
        a for a in rows
        if a.status.value == "missed"
        and a.starts_at is not None
        and a.starts_at.astimezone(timezone.utc).date() == yesterday
    ]
    return today_items, yesterday_missed


def collect_this_week(
    session_id: str, for_date: date, db_path: str | Path, now: datetime,
) -> list[Appointment]:
    """Return scheduled appointments in 7-day window minus today."""
    rows = scheduler.list_by_session(session_id, db_path=db_path)
    cutoff = now + timedelta(days=7)
    return [
        a for a in rows
        if a.status.value == "scheduled"
        and a.starts_at is not None
        and a.starts_at.astimezone(timezone.utc).date() != for_date
        and now <= a.starts_at <= cutoff
    ]


__all__ = [
    "collect_this_week",
    "collect_today",
    "collect_yesterday",
    "resolve_first_name",
]

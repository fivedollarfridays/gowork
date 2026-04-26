"""SQL loaders for the batched stall classifier (T13.90).

Extracted from :mod:`_batch_stalls` so that file stays inside the
arch file-size limit. Each loader issues a single SELECT scoped by
``WHERE session_id IN (...)`` and returns dicts keyed by session_id.
The loaders are deliberately raw — they read only the columns the
stall detector needs (no full row hydration) so this path remains
cheaper than the per-session :func:`compute_stall_for_session`.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path

from app.modules.common.temporal_types import coerce_to_aware_datetime

_AUTO_ADVANCE_EVENT_TYPE = "appointment_auto_advance"


def parse_iso(raw: str | None) -> datetime | None:
    """Parse an ISO-8601 string (possibly ending 'Z') into an aware datetime.

    Wraps :func:`app.modules.common.temporal_types.coerce_to_aware_datetime`
    to preserve the SQL-loader contract of returning ``None`` on absent or
    malformed inputs (rather than raising).
    """
    if not raw:
        return None
    try:
        return coerce_to_aware_datetime(raw)
    except ValueError:
        return None


def parse_date(raw: str | None) -> date | None:
    """Parse an ISO-8601 date string; tolerate trailing time components."""
    if not raw:
        return None
    head = raw.split("T", 1)[0].split(" ", 1)[0]
    try:
        return date.fromisoformat(head)
    except ValueError:
        return None


def _placeholders(n: int) -> str:
    """Return ``?, ?, ?`` for ``n`` placeholders (NULL when n=0)."""
    return ", ".join("?" for _ in range(n)) if n else "NULL"


def connect(db_path: str | Path) -> sqlite3.Connection:
    return sqlite3.connect(str(db_path))


def load_barriers(
    conn: sqlite3.Connection, session_ids: list[str],
) -> dict[str, list[str]]:
    """Return {session_id: [barrier_id, ...]} via one SELECT.

    Sessions whose ``barriers`` JSON is malformed or missing get an
    empty list, matching :func:`stall_detector._load_session_barriers`.
    """
    if not session_ids:
        return {}
    sql = (
        f"SELECT id, barriers FROM sessions "
        f"WHERE id IN ({_placeholders(len(session_ids))})"
    )
    out: dict[str, list[str]] = {sid: [] for sid in session_ids}
    for sid, raw in conn.execute(sql, session_ids).fetchall():
        if not raw:
            continue
        try:
            parsed = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            continue
        if isinstance(parsed, list):
            out[sid] = [b for b in parsed if isinstance(b, str)]
    return out


def load_attended_appointments(
    conn: sqlite3.Connection,
    session_ids: list[str],
    start: date,
    end: date,
) -> dict[str, list[tuple[str | None, datetime]]]:
    """Return {session_id: [(barrier_link, starts_at), ...]} for attended appts."""
    if not session_ids:
        return {}
    sql = (
        f"SELECT session_id, barrier_link, starts_at FROM appointments "
        f"WHERE status = 'attended' "
        f"AND session_id IN ({_placeholders(len(session_ids))})"
    )
    end_dt = datetime.combine(end, datetime.max.time(), tzinfo=timezone.utc)
    start_dt = datetime.combine(start, datetime.min.time(), tzinfo=timezone.utc)
    out: dict[str, list[tuple[str | None, datetime]]] = {
        sid: [] for sid in session_ids
    }
    for sid, barrier, starts_raw in conn.execute(sql, session_ids).fetchall():
        ts = parse_iso(starts_raw)
        if ts is None or not (start_dt <= ts <= end_dt):
            continue
        out[sid].append((barrier, ts))
    return out


def load_applied_applications(
    conn: sqlite3.Connection,
    session_ids: list[str],
    start: date,
    end: date,
) -> dict[str, list[datetime]]:
    """Return {session_id: [applied_at_utc, ...]} for APPLIED apps in window."""
    if not session_ids:
        return {}
    sql = (
        f"SELECT session_id, applied_date FROM job_applications "
        f"WHERE status = 'applied' "
        f"AND session_id IN ({_placeholders(len(session_ids))})"
    )
    out: dict[str, list[datetime]] = {sid: [] for sid in session_ids}
    for sid, applied_raw in conn.execute(sql, session_ids).fetchall():
        d = parse_date(applied_raw)
        if d is None or not (start <= d <= end):
            continue
        out[sid].append(
            datetime.combine(d, datetime.min.time(), tzinfo=timezone.utc),
        )
    return out


def load_outcomes(
    conn: sqlite3.Connection,
    session_ids: list[str],
    start: date,
    end: date,
) -> tuple[
    dict[str, list[datetime]],
    dict[str, list[str]],
]:
    """Return ({sid: outcome ts list}, {sid: signal_type list}).

    Auto-advance signals are filtered from the timestamp list (cannot
    indicate forward motion). The signal list keeps every event_type
    so callers can detect progression-event sessions.
    """
    ts_out: dict[str, list[datetime]] = {sid: [] for sid in session_ids}
    sig_out: dict[str, list[str]] = {sid: [] for sid in session_ids}
    if not session_ids:
        return ts_out, sig_out
    sql = (
        f"SELECT session_id, event_type, created_at FROM outcomes_records "
        f"WHERE session_id IN ({_placeholders(len(session_ids))})"
    )
    end_dt = datetime.combine(end, datetime.max.time(), tzinfo=timezone.utc)
    start_dt = datetime.combine(start, datetime.min.time(), tzinfo=timezone.utc)
    for sid, ev, created_raw in conn.execute(sql, session_ids).fetchall():
        ts = parse_iso(created_raw)
        if ts is None or not (start_dt <= ts <= end_dt):
            continue
        sig_out[sid].append(ev or "")
        if ev == _AUTO_ADVANCE_EVENT_TYPE:
            continue
        ts_out[sid].append(ts)
    return ts_out, sig_out


def load_progressed_app_ts(
    conn: sqlite3.Connection,
    session_ids: list[str],
    sessions_with_progression: set[str],
) -> dict[str, list[datetime]]:
    """Return {sid: [app.created_at, ...]} for INTERVIEW/OFFER apps.

    Only sessions in ``sessions_with_progression`` actually have
    timestamps loaded — others get an empty list. This mirrors
    :func:`evidence_collector._load_progressed_applications` which
    short-circuits when no in-window outcome carries a progression
    event type.
    """
    out: dict[str, list[datetime]] = {sid: [] for sid in session_ids}
    eligible = [sid for sid in session_ids if sid in sessions_with_progression]
    if not eligible:
        return out
    sql = (
        f"SELECT session_id, created_at FROM job_applications "
        f"WHERE status IN ('interview', 'offer') "
        f"AND session_id IN ({_placeholders(len(eligible))})"
    )
    for sid, created_raw in conn.execute(sql, eligible).fetchall():
        ts = parse_iso(created_raw)
        if ts is None:
            continue
        out[sid].append(ts)
    return out


__all__ = [
    "connect",
    "load_applied_applications",
    "load_attended_appointments",
    "load_barriers",
    "load_outcomes",
    "load_progressed_app_ts",
    "parse_date",
    "parse_iso",
]

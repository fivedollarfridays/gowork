"""Batch stall-classification helper (T13.90 — N+1 fix).

The original :func:`stall_detector.compute_stall_for_session` issues
~5 SELECTs per call. When the advisor inbox calls it inside a per-
session loop, the cost grows linearly with the cohort size — classic
N+1 (verified in ``backend/tests/test_n_plus_one_audit.py``: N=50
sessions = 252 SELECTs).

This module provides :func:`batch_compute_stalls`, a drop-in
replacement for the per-session loop that loads every signal stream
in a constant handful of batched ``WHERE session_id IN (...)`` queries
(see :mod:`_batch_stalls_io`) and runs the same pure classifier
helpers in Python — producing :class:`StalledSession`-equivalent
output with O(1) DB cost regardless of cohort size.

Scope
-----
Focused N+1 fix for the advisor-inbox list path
(:func:`app.modules.advisor.repository.list_stalled_sessions_for_city`).
Other callers of :func:`compute_stall_for_session` (single-session
detail lookups, the nightly orchestrator's per-session scan) keep the
existing per-session implementation — their query budget is already
constant relative to the response.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.modules.common.temporal_types import StallLevel
from app.modules.engagement import _batch_stalls_io as _io
from app.modules.engagement.classification import (
    BarrierStall,
    build_barrier_stalls,
    classify_days,
    days_between,
    latest_per_barrier,
    level_rank,
)

_LOOKBACK_DAYS = 90  # mirrors progress_signals._LOOKBACK_DAYS
_PROGRESSED_EVENT_TYPES: frozenset[str] = frozenset({
    "job_application_interview",
    "job_application_offer",
})


def _events_by_barrier(
    appt_rows: list[tuple[str | None, datetime]],
    applied_ts: list[datetime],
    progressed_ts: list[datetime],
    outcome_ts: list[datetime],
) -> dict[str | None, list[datetime]]:
    """Merge the four signal streams into the barrier-keyed map.

    Mirrors :func:`progress_signals.collect_progress_events` but
    operates on already-loaded lists rather than the EvidenceBundle.
    """
    out: dict[str | None, list[datetime]] = {}
    for barrier, ts in appt_rows:
        out.setdefault(barrier, []).append(ts)
    for ts in applied_ts:
        out.setdefault(None, []).append(ts)
    for ts in progressed_ts:
        out.setdefault(None, []).append(ts)
    for ts in outcome_ts:
        out.setdefault(None, []).append(ts)
    return out


def _classify_one(
    barriers: list[str],
    events_by_barrier: dict[str | None, list[datetime]],
    now: datetime,
) -> tuple[int, StallLevel, list[BarrierStall]]:
    """Return (days_stalled, stall_level, stalled_barriers) for one session."""
    if not barriers:
        global_events = events_by_barrier.get(None, [])
        latest = max(global_events) if global_events else None
        days = days_between(now, latest) if latest else 0
        level = classify_days(days) if latest else StallLevel.NONE
        return days, level, []
    latest_by_barrier = latest_per_barrier(events_by_barrier, barriers)
    stalls = build_barrier_stalls(latest_by_barrier, now)
    days = max((b.days_stalled for b in stalls), default=0)
    worst = max(
        (b.stall_level for b in stalls),
        key=level_rank,
        default=StallLevel.NONE,
    )
    return days, worst, stalls


def _load_all(
    session_ids: list[str], db_path: str | Path, now: datetime,
) -> tuple[
    dict[str, list[str]],
    dict[str, list[tuple[str | None, datetime]]],
    dict[str, list[datetime]],
    dict[str, list[datetime]],
    dict[str, list[datetime]],
]:
    """Issue every batched SELECT and return the five signal maps."""
    end = now.date()
    start = end - timedelta(days=_LOOKBACK_DAYS)
    conn = _io.connect(db_path)
    try:
        barriers = _io.load_barriers(conn, session_ids)
        appts = _io.load_attended_appointments(
            conn, session_ids, start, end,
        )
        applied = _io.load_applied_applications(
            conn, session_ids, start, end,
        )
        outcome_ts, outcome_sig = _io.load_outcomes(
            conn, session_ids, start, end,
        )
        progression_sessions = {
            sid for sid, sigs in outcome_sig.items()
            if any(s in _PROGRESSED_EVENT_TYPES for s in sigs)
        }
        progressed = _io.load_progressed_app_ts(
            conn, session_ids, progression_sessions,
        )
    finally:
        conn.close()
    return barriers, appts, applied, progressed, outcome_ts


def batch_compute_stalls(
    session_ids: list[str],
    *,
    db_path: str | Path,
    now: datetime | None = None,
) -> dict[str, tuple[int, StallLevel, list[BarrierStall]]]:
    """Return a stall summary per session id, all in O(1) queries.

    The returned mapping has shape::

        {session_id: (days_stalled, stall_level, stalled_barriers)}

    Sessions absent from ``session_ids`` are not present in the result.
    Empty ``session_ids`` returns an empty dict (no SQL is executed).
    """
    if not session_ids:
        return {}
    now = now or datetime.now(timezone.utc)
    barriers, appts, applied, progressed, outcome_ts = _load_all(
        session_ids, db_path, now,
    )
    out: dict[str, tuple[int, StallLevel, list[BarrierStall]]] = {}
    for sid in session_ids:
        events = _events_by_barrier(
            appts.get(sid, []),
            applied.get(sid, []),
            progressed.get(sid, []),
            outcome_ts.get(sid, []),
        )
        out[sid] = _classify_one(barriers.get(sid, []), events, now)
    return out


__all__ = ["batch_compute_stalls"]

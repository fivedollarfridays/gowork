"""Stall classification helpers (T12.18 helper).

Pure functions: threshold classification, date math, and per-barrier
reduction of event timestamps into BarrierStall entries. Extracted from
stall_detector.py to keep that module inside the arch file-size warning
threshold.

All functions here are side-effect free and trivially testable.
"""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel

from app.modules.common.temporal_types import StallLevel

SOFT_DAYS = 3
MEDIUM_DAYS = 7
HARD_DAYS = 14
AUTO_ADVANCE_SUPPRESS_HOURS = 48


class BarrierStall(BaseModel):
    """Stall classification for a single barrier the session is working on."""

    barrier_id: str
    days_stalled: int
    stall_level: StallLevel


_LEVEL_RANK: dict[StallLevel, int] = {
    StallLevel.NONE: 0,
    StallLevel.SOFT: 1,
    StallLevel.MEDIUM: 2,
    StallLevel.HARD: 3,
}


def classify_days(days: int) -> StallLevel:
    """Map integer calendar-day count to a StallLevel."""
    if days >= HARD_DAYS:
        return StallLevel.HARD
    if days >= MEDIUM_DAYS:
        return StallLevel.MEDIUM
    if days >= SOFT_DAYS:
        return StallLevel.SOFT
    return StallLevel.NONE


def level_rank(level: StallLevel) -> int:
    """Numeric rank for severity comparisons (higher = worse)."""
    return _LEVEL_RANK[level]


def days_between(later: datetime, earlier: datetime) -> int:
    """Calendar-day floor between two aware UTC datetimes."""
    if earlier.tzinfo is None:
        earlier = earlier.replace(tzinfo=timezone.utc)
    if later.tzinfo is None:
        later = later.replace(tzinfo=timezone.utc)
    return max(0, (later - earlier).days)


def latest_per_barrier(
    events_by_barrier: dict[str | None, list[datetime]],
    barriers: list[str],
) -> dict[str, datetime | None]:
    """Reduce event timestamps to a per-barrier latest.

    Precedence per barrier:
      1. Signals directly tagged with this barrier_id
      2. Fallback to session-wide (`None` key) signals
    Other barriers' signals do NOT bleed over — a worker active on DMV
    last week but untouched on childcare for a month is still stalled
    on childcare.
    """
    global_events = events_by_barrier.get(None, [])
    result: dict[str, datetime | None] = {}
    for barrier_id in barriers:
        per = events_by_barrier.get(barrier_id, [])
        if per:
            result[barrier_id] = max(per)
        elif global_events:
            result[barrier_id] = max(global_events)
        else:
            result[barrier_id] = None
    return result


def build_barrier_stalls(
    latest_by_barrier: dict[str, datetime | None],
    now: datetime,
) -> list[BarrierStall]:
    """Materialize BarrierStall entries from per-barrier latest timestamps.

    Barriers with no signal at all are omitted — without a baseline
    timestamp we cannot compute a meaningful "days since".
    """
    stalls: list[BarrierStall] = []
    for barrier_id, last_ts in latest_by_barrier.items():
        if last_ts is None:
            continue
        days = days_between(now, last_ts)
        stalls.append(BarrierStall(
            barrier_id=barrier_id,
            days_stalled=days,
            stall_level=classify_days(days),
        ))
    return stalls


__all__ = [
    "AUTO_ADVANCE_SUPPRESS_HOURS",
    "BarrierStall",
    "HARD_DAYS",
    "MEDIUM_DAYS",
    "SOFT_DAYS",
    "build_barrier_stalls",
    "classify_days",
    "days_between",
    "latest_per_barrier",
    "level_rank",
]

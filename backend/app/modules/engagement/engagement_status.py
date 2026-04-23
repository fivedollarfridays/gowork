"""Engagement status — enriched per-session status struct (T12.18).

Port of `ops:lib/engagement_status.py` shape, city-generic and adapted
for MontGoWork's session+barrier domain. The ops version is Reddit-
specific (thread replies, post metrics, conversion funnels); we keep
only the enriched-status shape (last action date, days since, stall
level, recommendations) and derive those from the stall detector
rather than from ad-sync freshness.

`_get_recommendations` is ported structurally: returns a list of
`{"type", "message", "urgency"}` dicts driven by the stall level.
Extracted into its own module so the detector can stay lean and
callers can import the recommender without pulling in the full
scan loop.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel

from app.modules.common.temporal_types import StallLevel
from app.modules.engagement.stall_detector import (
    BarrierStall,
    compute_stall_for_session,
)


class EngagementStatus(BaseModel):
    """Enriched engagement status for a single session."""

    session_id: str
    last_action_date: datetime | None
    days_since_last_action: int
    stall_level: StallLevel
    stalled_barriers: list[BarrierStall]
    recommendations: list[dict]


def _get_recommendations(
    stall_level: StallLevel,
    days_since: int,
    stalled_barriers: list[BarrierStall],
) -> list[dict]:
    """Return actionable recommendations keyed off stall level."""
    if stall_level is StallLevel.NONE:
        return [{
            "type": "on_track",
            "message": "Recent activity logged; keep momentum.",
            "urgency": "low",
        }]

    recs: list[dict] = [{
        "type": f"stall_{stall_level.value}",
        "message": _stall_message(stall_level, days_since),
        "urgency": _urgency_for(stall_level),
    }]

    worst = _worst_barrier(stalled_barriers)
    if worst is not None and worst.stall_level is not StallLevel.NONE:
        recs.append({
            "type": "barrier_focus",
            "message": (
                f"Focus on barrier '{worst.barrier_id}' "
                f"({worst.days_stalled}d since last progress)."
            ),
            "urgency": _urgency_for(worst.stall_level),
        })
    return recs


def _stall_message(level: StallLevel, days: int) -> str:
    """Craft a short user-facing message for the given stall level."""
    labels = {
        StallLevel.SOFT: "Light stall",
        StallLevel.MEDIUM: "Moderate stall",
        StallLevel.HARD: "Extended stall",
    }
    prefix = labels.get(level, "Stall")
    return f"{prefix}: {days}d since last progress."


def _urgency_for(level: StallLevel) -> str:
    """Map stall level to an urgency label."""
    return {
        StallLevel.NONE: "low",
        StallLevel.SOFT: "low",
        StallLevel.MEDIUM: "medium",
        StallLevel.HARD: "high",
    }[level]


def _worst_barrier(
    stalled_barriers: list[BarrierStall],
) -> BarrierStall | None:
    """Return the barrier with the highest days_stalled, or None if empty."""
    if not stalled_barriers:
        return None
    return max(stalled_barriers, key=lambda b: b.days_stalled)


def _last_action_timestamp(
    session_id: str,
    db_path: str | Path,
    now: datetime,
) -> datetime | None:
    """Infer the most-recent progress timestamp from the stall detector.

    We re-run the same signal collector to derive the latest event so
    callers don't need to reach into two modules for the same answer.
    """
    from app.modules.engagement.progress_signals import (
        collect_progress_events,
    )
    events = collect_progress_events(
        session_id, db_path=db_path, now=now,
    )
    flat: list[datetime] = []
    for tss in events.values():
        flat.extend(tss)
    return max(flat) if flat else None


def get_engagement_status(
    session_id: str,
    *,
    db_path: str | Path,
    now: datetime | None = None,
) -> EngagementStatus:
    """Return enriched engagement status for a session."""
    now = now or datetime.now(timezone.utc)
    stalled = compute_stall_for_session(
        session_id, db_path=db_path, now=now,
    )
    last_ts = _last_action_timestamp(session_id, db_path, now)
    recs = _get_recommendations(
        stalled.stall_level,
        stalled.days_stalled,
        stalled.stalled_barriers,
    )
    return EngagementStatus(
        session_id=session_id,
        last_action_date=last_ts,
        days_since_last_action=stalled.days_stalled,
        stall_level=stalled.stall_level,
        stalled_barriers=stalled.stalled_barriers,
        recommendations=recs,
    )


__all__ = ["EngagementStatus", "get_engagement_status"]

"""DB queries for the outcome intelligence engine.

Joins visit_feedback with sessions to produce per-barrier feedback
observations that the intelligence engine can aggregate.

The outcomes column in visit_feedback is a JSON array of barrier IDs
that the user reports having resolved. We cross-reference these with
the session's barriers list to determine which barriers were resolved
and which were not.

When both sessions.created_at and visit_feedback.submitted_at are
available, we estimate weeks_to_resolve from the time delta for
resolved barriers.
"""

import json
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


def _estimate_weeks(created_at: str | None, submitted_at: str | None) -> float | None:
    """Estimate weeks between session creation and feedback submission.

    Returns None if either timestamp is missing or unparseable.
    """
    if not created_at or not submitted_at:
        return None
    try:
        fmt_candidates = ["%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S%z",
                          "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"]
        c = _try_parse(created_at, fmt_candidates)
        s = _try_parse(submitted_at, fmt_candidates)
        if c is None or s is None:
            return None
        delta = (s - c).total_seconds()
        weeks = max(delta / (7 * 24 * 3600), 0.1)
        return round(weeks, 1)
    except (ValueError, TypeError):
        return None


def _try_parse(ts: str, formats: list[str]) -> datetime | None:
    """Try parsing a timestamp with multiple format candidates."""
    for fmt in formats:
        try:
            return datetime.strptime(ts, fmt)
        except ValueError:
            continue
    return None


def _parse_feedback_row(
    barriers_str: str | None,
    outcomes_str: str | None,
    plan_accuracy: int | None,
    weeks_estimate: float | None = None,
) -> list[dict]:
    """Parse a single feedback row into per-barrier observations."""
    barriers = _safe_parse_list(barriers_str)
    if not barriers:
        return []

    resolved_set = set(_safe_parse_list(outcomes_str))
    observations: list[dict] = []
    for bid in barriers:
        if not isinstance(bid, str):
            continue
        is_resolved = bid in resolved_set
        observations.append({
            "barrier_id": bid,
            "resolved": is_resolved,
            "weeks_to_resolve": weeks_estimate if is_resolved else None,
            "plan_accuracy": plan_accuracy,
        })
    return observations


async def get_barrier_feedback_rows(
    db: AsyncSession,
) -> list[dict]:
    """Read visit feedback joined with session barriers.

    Returns a flat list of per-barrier observations:
      - barrier_id: str
      - resolved: bool (True if barrier_id appears in outcomes)
      - weeks_to_resolve: float | None (estimated from timestamps)
      - plan_accuracy: int

    Only sessions that have visit_feedback are included.
    """
    result = await db.execute(
        text(
            "SELECT s.barriers, vf.outcomes, vf.plan_accuracy, "
            "s.created_at, vf.submitted_at "
            "FROM visit_feedback vf "
            "JOIN sessions s ON s.id = vf.session_id"
        ),
    )
    rows_raw = result.fetchall()

    observations: list[dict] = []
    for row in rows_raw:
        weeks = _estimate_weeks(row[3], row[4])
        observations.extend(
            _parse_feedback_row(row[0], row[1], row[2], weeks)
        )
    return observations


def _safe_parse_list(raw: str | None) -> list:
    """Parse a JSON string to list, returning empty list on failure."""
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return parsed
        return []
    except (json.JSONDecodeError, TypeError):
        return []

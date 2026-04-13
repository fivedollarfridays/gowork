"""DB queries for the outcome intelligence engine.

Joins visit_feedback with sessions to produce per-barrier feedback
observations that the intelligence engine can aggregate.

The outcomes column in visit_feedback is a JSON array of barrier IDs
that the user reports having resolved. We cross-reference these with
the session's barriers list to determine which barriers were resolved
and which were not.
"""

import json

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def get_barrier_feedback_rows(
    db: AsyncSession,
) -> list[dict]:
    """Read visit feedback joined with session barriers.

    Returns a flat list of per-barrier observations:
      - barrier_id: str
      - resolved: bool (True if barrier_id appears in outcomes)
      - weeks_to_resolve: None (not tracked per-barrier yet)
      - plan_accuracy: int

    Only sessions that have visit_feedback are included.
    """
    result = await db.execute(
        text(
            "SELECT s.barriers, vf.outcomes, vf.plan_accuracy "
            "FROM visit_feedback vf "
            "JOIN sessions s ON s.id = vf.session_id"
        ),
    )
    rows_raw = result.fetchall()

    observations: list[dict] = []
    for row in rows_raw:
        barriers_str, outcomes_str, plan_accuracy = row[0], row[1], row[2]

        # Parse barriers
        barriers = _safe_parse_list(barriers_str)
        if not barriers:
            continue

        # Parse outcomes (resolved barrier IDs)
        resolved_set = set(_safe_parse_list(outcomes_str))

        for bid in barriers:
            if not isinstance(bid, str):
                continue
            observations.append({
                "barrier_id": bid,
                "resolved": bid in resolved_set,
                "weeks_to_resolve": None,  # Not tracked per-barrier yet
                "plan_accuracy": plan_accuracy,
            })

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

"""Barrier graph queries -- top-N resources for a set of barriers."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def get_top_resources_for_barriers(
    session: AsyncSession, barrier_ids: list[str], n: int = 5
) -> list[dict]:
    """Return the top-N resources for a set of barriers, ordered by impact_strength.

    Deduplicates resources across barriers (takes max impact_strength).
    Excludes resources with health_status = 'hidden'.
    """
    if not barrier_ids:
        return []

    placeholders = ", ".join(f":b{i}" for i in range(len(barrier_ids)))
    params: dict = {f"b{i}": bid for i, bid in enumerate(barrier_ids)}
    params["n"] = n

    result = await session.execute(
        text(
            f"SELECT r.*, MAX(br.impact_strength) AS impact_strength, "
            f"br.resource_id "
            f"FROM barrier_resources br "
            f"JOIN resources r ON br.resource_id = r.id "
            f"WHERE br.barrier_id IN ({placeholders}) "
            f"AND r.health_status != 'hidden' "
            f"GROUP BY br.resource_id "
            f"ORDER BY impact_strength DESC "
            f"LIMIT :n"
        ),
        params,
    )
    return [dict(row._mapping) for row in result]

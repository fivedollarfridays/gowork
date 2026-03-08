"""Barrier graph query functions — top-N resource retrieval."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


def _build_top_resources_query(barrier_ids: list[str]) -> tuple[str, dict]:
    """Build parameterized SQL + params for top-resources query."""
    placeholders = ", ".join(f":b{i}" for i in range(len(barrier_ids)))
    params = {f"b{i}": bid for i, bid in enumerate(barrier_ids)}
    sql = (
        f"SELECT r.id, r.name, r.category, r.subcategory, "
        f"SUM(br.impact_strength) AS score "
        f"FROM barrier_resources br "
        f"JOIN resources r ON r.id = br.resource_id "
        f"WHERE br.barrier_id IN ({placeholders}) "
        f"AND (r.health_status IS NULL OR r.health_status != 'HIDDEN') "
        f"GROUP BY r.id, r.name, r.category, r.subcategory "
        f"ORDER BY score DESC "
        f"LIMIT :n"
    )
    return sql, params


async def get_top_resources_for_barriers(
    db: AsyncSession,
    barrier_ids: list[str],
    n: int = 5,
) -> list[dict]:
    """Return top N resources ranked by combined impact_strength across barriers.

    Excludes resources with health_status = 'HIDDEN'.
    Results sorted by aggregate score descending.
    """
    if not barrier_ids:
        return []

    sql, params = _build_top_resources_query(barrier_ids)
    params["n"] = n
    result = await db.execute(text(sql), params)
    return [
        {"id": r[0], "name": r[1], "category": r[2], "subcategory": r[3], "score": r[4]}
        for r in result.fetchall()
    ]

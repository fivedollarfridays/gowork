"""Barrier graph traversal — BFS root detection and priority sorting."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# Category priority order (lower = higher priority)
_CATEGORY_PRIORITY: dict[str, int] = {
    "childcare": 1,
    "transportation": 2,
    "credit": 3,
    "criminal": 4,
    "housing": 5,
    "employment": 6,
    "training": 7,
}

_DEFAULT_PRIORITY = 99


def _category_priority(category: str) -> int:
    return _CATEGORY_PRIORITY.get(category.lower(), _DEFAULT_PRIORITY)


async def _get_barrier_info(
    barrier_ids: list[str], db: AsyncSession
) -> dict[str, dict]:
    """Fetch id, name, category for the given barrier_ids."""
    if not barrier_ids:
        return {}
    placeholders = ", ".join(f":b{i}" for i in range(len(barrier_ids)))
    params = {f"b{i}": bid for i, bid in enumerate(barrier_ids)}
    result = await db.execute(
        text(f"SELECT id, name, category FROM barriers WHERE id IN ({placeholders})"),
        params,
    )
    return {
        row[0]: {"id": row[0], "name": row[1], "category": row[2]}
        for row in result.fetchall()
    }


async def _get_incoming_causes(
    barrier_ids: list[str], db: AsyncSession
) -> set[str]:
    """Return barrier_ids that have at least one incoming CAUSES edge within the set."""
    if not barrier_ids:
        return set()
    placeholders = ", ".join(f":b{i}" for i in range(len(barrier_ids)))
    src_placeholders = ", ".join(f":s{i}" for i in range(len(barrier_ids)))
    params = {f"b{i}": bid for i, bid in enumerate(barrier_ids)}
    params.update({f"s{i}": bid for i, bid in enumerate(barrier_ids)})
    result = await db.execute(
        text(
            f"SELECT DISTINCT target_barrier_id "
            f"FROM barrier_relationships "
            f"WHERE relationship_type = 'CAUSES' "
            f"AND target_barrier_id IN ({placeholders}) "
            f"AND source_barrier_id IN ({src_placeholders})"
        ),
        params,
    )
    return {row[0] for row in result.fetchall()}


async def find_root_barriers(
    barrier_ids: list[str], db: AsyncSession
) -> list[dict]:
    """Return barriers with no incoming CAUSES edges within the provided set.

    Sorted by category priority: childcare=1, transportation=2, credit=3...
    Each entry is a dict with at least {"id", "category"}.
    """
    if not barrier_ids:
        return []

    info = await _get_barrier_info(barrier_ids, db)
    has_incoming = await _get_incoming_causes(barrier_ids, db)

    roots = [v for k, v in info.items() if k not in has_incoming]
    roots.sort(key=lambda b: _category_priority(b["category"]))
    return roots

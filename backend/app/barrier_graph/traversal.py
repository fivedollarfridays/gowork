"""Barrier graph traversal -- find root barriers via relationship analysis."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

_CATEGORY_PRIORITY = {
    "childcare": 1,
    "transportation": 2,
    "housing": 3,
    "health": 4,
    "credit": 5,
    "criminal": 6,
    "training": 7,
    "employment": 8,
}


async def find_root_barriers(
    barrier_ids: list[str], db: AsyncSession
) -> list[dict]:
    """Find barriers with no incoming CAUSES edges within the user's barrier set.

    Returns barrier dicts sorted by category priority (childcare first).
    """
    if not barrier_ids:
        return []

    barrier_set = set(barrier_ids)

    # Find which barriers in the set are targets of CAUSES from other barriers in the set
    caused_targets = await _find_caused_targets(db, barrier_ids)

    # Root barriers = those not caused by another barrier in the set
    root_ids = [bid for bid in barrier_ids if bid not in caused_targets]
    if not root_ids:
        # All barriers cause each other (cycle) — return all
        root_ids = list(barrier_ids)

    # Fetch barrier metadata
    roots = await _fetch_barriers(db, root_ids)
    roots.sort(key=lambda b: _CATEGORY_PRIORITY.get(b["category"], 99))
    return roots


async def _find_caused_targets(
    db: AsyncSession, barrier_ids: list[str]
) -> set[str]:
    """Find barrier_ids that are targets of CAUSES relationships from other barriers in the set."""
    placeholders = ", ".join(f":b{i}" for i in range(len(barrier_ids)))
    params = {f"b{i}": bid for i, bid in enumerate(barrier_ids)}
    result = await db.execute(
        text(
            f"SELECT DISTINCT target_barrier_id FROM barrier_relationships "
            f"WHERE source_barrier_id IN ({placeholders}) "
            f"AND target_barrier_id IN ({placeholders}) "
            f"AND relationship_type = 'CAUSES'"
        ),
        params,
    )
    return {row[0] for row in result}


async def _fetch_barriers(
    db: AsyncSession, barrier_ids: list[str]
) -> list[dict]:
    """Fetch barrier rows by IDs."""
    if not barrier_ids:
        return []
    placeholders = ", ".join(f":b{i}" for i in range(len(barrier_ids)))
    params = {f"b{i}": bid for i, bid in enumerate(barrier_ids)}
    result = await db.execute(
        text(
            f"SELECT id, name, category, description, playbook "
            f"FROM barriers WHERE id IN ({placeholders})"
        ),
        params,
    )
    return [dict(row._mapping) for row in result]

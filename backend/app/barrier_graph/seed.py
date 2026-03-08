"""Barrier graph seed data loader -- idempotent upsert of barrier nodes and edges."""

import json
import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import _resolve_data_dir

logger = logging.getLogger(__name__)


async def upsert_barrier_graph(session: AsyncSession) -> None:
    """Idempotently insert barrier nodes and edges. Safe to call multiple times."""
    _SEED_FILE = _resolve_data_dir() / "barrier_graph_seed.json"
    if not _SEED_FILE.exists():
        logger.warning("barrier_graph_seed.json not found at %s", _SEED_FILE)
        return

    data = json.loads(_SEED_FILE.read_text())
    barriers = data.get("barriers", [])
    relationships = data.get("relationships", [])

    await _upsert_barriers(session, barriers)
    await _upsert_relationships(session, relationships)
    await session.commit()
    logger.info(
        "Barrier graph seeded: %d nodes, %d edges",
        len(barriers),
        len(relationships),
    )


async def _upsert_barriers(session: AsyncSession, barriers: list[dict]) -> None:
    for barrier in barriers:
        await session.execute(
            text(
                "INSERT OR IGNORE INTO barriers "
                "(id, name, category, description, playbook) "
                "VALUES (:id, :name, :category, :description, :playbook)"
            ),
            {
                "id": barrier["id"],
                "name": barrier["name"],
                "category": barrier["category"],
                "description": barrier.get("description", ""),
                "playbook": barrier.get("playbook", ""),
            },
        )


async def _upsert_relationships(
    session: AsyncSession, relationships: list[dict]
) -> None:
    for rel in relationships:
        await session.execute(
            text(
                "INSERT OR IGNORE INTO barrier_relationships "
                "(source_barrier_id, target_barrier_id, relationship_type, weight) "
                "VALUES (:src, :tgt, :rel_type, :weight)"
            ),
            {
                "src": rel["source"],
                "tgt": rel["target"],
                "rel_type": rel["relationship_type"],
                "weight": rel.get("weight", 1.0),
            },
        )

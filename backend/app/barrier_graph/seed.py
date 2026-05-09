"""Barrier graph seed data loader -- idempotent upsert of barrier nodes and edges.

Per-city positional resource_id translation
-------------------------------------------

Each city's ``data/cities/<slug>/barrier_graph_seed.json`` references
``resource_id`` values 1..N, where N = the number of entries in that
city's ``resources.json``. Those positional IDs are stable WITHIN the
city's seed but DO NOT match the global auto-increment IDs assigned
when ``seed_resources_all_cities`` loads every city's resources into
the single ``resources`` table.

Example (alphabetical city load order: dallas, fort-worth, montgomery):

    Dallas resources.json (10 entries) -> global ids 1..10
    FW resources.json (74 entries)     -> global ids 11..84

    FW barrier_graph_seed.json says resource_id=1 — meant to point at
    FW's first resource (Workforce Solutions for Tarrant County, global
    id=11), but a naive insert would point at Dallas's id=1
    (Workforce Solutions Greater Dallas).

This loader is invoked once per request with the active city's
``resolve_data_dir()``, so the active city slug determines which
resources to look up. We translate JSON positional IDs to global IDs
by querying ``resources WHERE city = <active>`` ordered by global id;
the Nth row corresponds to the JSON's 1-indexed position N.

Pre-S25 history: this bug was latent because Montgomery used the legacy
fallback bundle (no resources.json -> 0 multi-city rows) and FW was
the only city with resources.json. FW's positional IDs happened to
equal its global IDs because FW was the only city loaded. Adding
Dallas in S25 made the gap visible (caught by
test_corpus_includes_resources_and_playbooks).
"""

import json
import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.cities.config import get_city_config
from app.core.database import resolve_data_dir

logger = logging.getLogger(__name__)


async def upsert_barrier_graph(session: AsyncSession) -> None:
    """Idempotently insert barrier nodes and edges. Safe to call multiple times."""
    _SEED_FILE = resolve_data_dir() / "barrier_graph_seed.json"
    if not _SEED_FILE.exists():
        logger.warning("barrier_graph_seed.json not found at %s", _SEED_FILE)
        return

    data = json.loads(_SEED_FILE.read_text())
    barriers = data.get("barriers", [])
    relationships = data.get("relationships", [])
    barrier_resources = data.get("barrier_resources", [])

    await _upsert_barriers(session, barriers)
    await _upsert_relationships(session, relationships)
    await _upsert_barrier_resources(session, barrier_resources)
    await session.commit()
    logger.info(
        "Barrier graph seeded: %d nodes, %d edges, %d resource links",
        len(barriers),
        len(relationships),
        len(barrier_resources),
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


async def _build_positional_id_map(session: AsyncSession) -> dict[int, int]:
    """Map this city's 1-indexed positional resource_id to its global DB id.

    Returns ``{}`` if the ``resources`` table has no ``city`` column
    (pre-m008 fallback). In that case the loader emits the JSON's
    resource_id verbatim — preserving legacy single-city behaviour.

    Uses the active city slug from ``get_city_config()``. If the seed
    file references a position outside the [1..N] range for that city,
    the row is skipped with a warning rather than producing a dangling
    FK to another city's resource.
    """
    has_city_col = await session.execute(text("PRAGMA table_info(resources)"))
    if not any(row[1] == "city" for row in has_city_col.fetchall()):
        return {}

    # The resources table is tagged with the city slug (e.g. "fort-worth"),
    # not the display name. Derive the slug from CityConfig.data_dir which
    # is "data/cities/<slug>" by convention; the trailing path segment IS
    # the slug.
    cfg = get_city_config()
    city_slug = cfg.data_dir.rsplit("/", 1)[-1]
    slug_query = text(
        "SELECT id FROM resources WHERE city = :city ORDER BY id ASC"
    )
    result = await session.execute(slug_query, {"city": city_slug})
    global_ids = [row[0] for row in result.fetchall()]
    return {pos: gid for pos, gid in enumerate(global_ids, start=1)}


async def _upsert_barrier_resources(
    session: AsyncSession, barrier_resources: list[dict]
) -> None:
    """Upsert barrier↔resource edges, translating positional resource_ids.

    See module docstring for the per-city positional-id contract. Skips
    rows whose JSON resource_id falls outside the active city's [1..N]
    range — that's a seed-data bug worth a warning, not a silent FK to
    another city's resource.
    """
    id_map = await _build_positional_id_map(session)
    skipped: list[int] = []
    for br in barrier_resources:
        json_resource_id = br["resource_id"]
        # Translate when we have a city-scoped map; otherwise emit verbatim
        # (legacy single-city / pre-m008 fallback).
        if id_map:
            global_id = id_map.get(json_resource_id)
            if global_id is None:
                skipped.append(json_resource_id)
                continue
        else:
            global_id = json_resource_id
        await session.execute(
            text(
                "INSERT OR IGNORE INTO barrier_resources "
                "(barrier_id, resource_id, impact_strength, notes) "
                "VALUES (:barrier_id, :resource_id, :impact_strength, :notes)"
            ),
            {
                "barrier_id": br["barrier_id"],
                "resource_id": global_id,
                "impact_strength": br["impact_strength"],
                "notes": br.get("notes", ""),
            },
        )
    if skipped:
        logger.warning(
            "barrier_graph_seed.json references resource_ids outside the "
            "active city's [1..N] range; %d rows skipped (positions=%s)",
            len(skipped), skipped,
        )

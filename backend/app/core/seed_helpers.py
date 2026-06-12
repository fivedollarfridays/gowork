"""Seeding helpers — extracted from ``app.core.database`` to keep
that module within the project's max-functions-per-file ceiling.

The functions here own three concerns:

* **Migration plumbing** — bridging the async SQLAlchemy world to the
  sync ``sqlite3`` migration runner (``apply_pending_migrations``).
* **City-aware resource seeding** — discovering every configured city
  and tagging each ``resources`` row with its source slug
  (``seed_resources_all_cities``).
* **Generic seed I/O** — reading a JSON file and inserting its rows
  into a single table (``seed_from_file``), used both by the multi-
  city resources path and the legacy single-city tables.
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path

from sqlalchemy import text

from app.core.schema import ALLOWED_COLUMNS, JSON_FIELDS

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_DEFAULT_DATA_DIR = _PROJECT_ROOT / "data"

# Map of city-agnostic filename -> ordered fallback files inside the
# legacy ``data/`` bundle.  Used when a city's directory has no direct
# replacement.  The ``resources.json`` fallback dates back to the
# Montgomery-only seed era; later cities ship a single ``resources.json``.
LEGACY_FALLBACKS: dict[str, list[str]] = {
    "employers.json": ["montgomery_businesses.json"],
    "resources.json": [
        "career_centers.json", "training_programs.json",
        "childcare_providers.json", "community_resources.json",
    ],
}


def validate_seed_record(table: str, record: dict) -> dict:
    """Validate and clean a seed record before SQL interpolation.

    Raises ValueError if table is not in ALLOWED_COLUMNS.
    Filters record to only allowed columns and serializes JSON fields.
    """
    if table not in ALLOWED_COLUMNS:
        raise ValueError(f"Unknown seed table: {table!r}")
    allowed = ALLOWED_COLUMNS[table]
    clean = {k: v for k, v in record.items() if k in allowed}
    for field in JSON_FIELDS:
        if field in clean and isinstance(clean[field], (list, dict)):
            clean[field] = json.dumps(clean[field])
    return clean


async def apply_pending_migrations(engine) -> None:
    """Apply m002+ migrations through the sync sqlite3 runner."""
    db_path = extract_db_path(engine.url)
    if not db_path:
        return  # in-memory or non-sqlite URL — runner can't help

    from app.core.migrations import runner

    await asyncio.to_thread(runner.apply_pending, db_path)


def extract_db_path(url) -> str | None:
    """Pull the on-disk filename out of a sqlite SQLAlchemy URL.

    Returns ``None`` for ``:memory:`` or non-sqlite URLs so the caller
    can short-circuit cleanly.
    """
    drivername = getattr(url, "drivername", "") or ""
    if "sqlite" not in drivername:
        return None
    database = getattr(url, "database", None)
    if not database or database == ":memory:":
        return None
    return database


def is_real_project_data_dir(data_dir: Path) -> bool:
    """Return True if *data_dir* is rooted under the project ``data/``.

    Tests patch ``resolve_data_dir`` to a temp directory; in that case
    we want the legacy single-dir seed path, not the multi-city scan
    of ``cities/*.yaml``.  A path is "real" iff it sits inside the
    project's data tree.
    """
    try:
        data_dir.resolve().relative_to(_DEFAULT_DATA_DIR.resolve())
        return True
    except (ValueError, OSError):
        return False


def resolve_seed_files(data_dir: Path, filename: str) -> list[Path]:
    """Resolve seed file path, trying legacy fallbacks if needed."""
    primary = data_dir / filename
    if primary.exists():
        return [primary]
    fallbacks = LEGACY_FALLBACKS.get(filename, [])
    found = [data_dir / fb for fb in fallbacks if (data_dir / fb).exists()]
    return found


def city_resource_seed_files(slug: str) -> list[Path]:
    """Return all resource seed files for a city, in priority order.

    Looks for ``data/cities/<slug>/resources.json`` first; if absent,
    falls through to the legacy bundle inside the city's OWN directory
    (career_centers, training_programs, childcare_providers,
    community_resources).  Crucially, this does NOT fall back to the
    project-level ``data/`` bundle — that silent cross-city leak is
    what caused Fort Worth deployments to surface Montgomery, AL data
    when a city-specific ``resources.json`` was missing.
    """
    city_dir = _PROJECT_ROOT / "data" / "cities" / slug
    primary = city_dir / "resources.json"
    if primary.exists():
        return [primary]
    fallbacks = LEGACY_FALLBACKS.get("resources.json", [])
    found = [city_dir / fb for fb in fallbacks if (city_dir / fb).exists()]
    if not found:
        logger.warning(
            "No resources seed files found for city %r in %s "
            "(neither resources.json nor legacy bundle).",
            slug, city_dir,
        )
    return found


def all_city_slugs() -> list[str]:
    """Return slugs of every city YAML found in ``cities/``."""
    cities_dir = _PROJECT_ROOT / "cities"
    if not cities_dir.is_dir():
        return []
    return sorted(p.stem for p in cities_dir.glob("*.yaml"))


async def resources_has_city_column(conn) -> bool:
    """Return True if the ``resources`` table has a ``city`` column."""
    res = await conn.execute(text("PRAGMA table_info(resources)"))
    return any(row[1] == "city" for row in res.fetchall())


async def _curated_resource_keys(conn) -> set[tuple[str | None, str | None]]:
    """Return ``(city, name)`` keys for resources with admin curation set.

    Used by ``seed_from_file`` to skip re-seeding rows an admin has
    edited (T26.1 contract: ``user_curated_at IS NOT NULL`` means
    "preserve"). Returns an empty set when the column is absent —
    pre-0015 deployments can't have curated rows by definition.
    """
    cols = await conn.execute(text("PRAGMA table_info(resources)"))
    if not any(row[1] == "user_curated_at" for row in cols.fetchall()):
        return set()
    res = await conn.execute(text(
        "SELECT city, name FROM resources WHERE user_curated_at IS NOT NULL"
    ))
    return {(row[0], row[1]) for row in res.fetchall()}


async def seed_resources_all_cities(conn) -> None:
    """Seed the ``resources`` table once per configured city, tagged.

    Each row inherits the city slug as its ``city`` column so the
    matching pipeline can filter by per-request context.  Cities
    without a dedicated ``resources.json`` fall back to the legacy
    Montgomery bundle (career_centers + community_resources +
    training_programs + childcare_providers) — currently this only
    applies to the ``montgomery`` slug.

    Requires the m008 ``resources.city`` column.  If the column
    isn't present (caller skipped migrations) we tag with ``None``
    so the legacy single-city behaviour still produces rows.
    """
    has_city = await resources_has_city_column(conn)
    for slug in all_city_slugs():
        for filepath in city_resource_seed_files(slug):
            await seed_from_file(
                conn, filepath, "resources",
                city_slug=slug if has_city else None,
            )


async def _insert_seed_record(conn, table: str, clean: dict) -> None:
    """Insert one validated seed record into *table*.

    SAFETY: table comes from a hardcoded seed map; columns are filtered
    against ALLOWED_COLUMNS; values are parameterised via :key binding.
    No user input reaches this SQL builder.
    """
    columns = ", ".join(clean.keys())
    placeholders = ", ".join(f":{k}" for k in clean.keys())
    await conn.execute(
        text(f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"),
        clean,
    )


async def seed_from_file(
    conn, filepath: Path, table: str, *, city_slug: str | None = None,
) -> None:
    """Load a single seed file into the given table.

    When *city_slug* is provided AND the table accepts a ``city``
    column, every inserted row is tagged with that slug. Pre-tagged
    JSON files keep their explicit ``city`` value.

    For the ``resources`` table, rows with the same ``(city, name)``
    as an existing admin-curated row (``user_curated_at IS NOT NULL``)
    are skipped — preserving manual edits across container restarts
    (T26.1 contract).
    """
    data = json.loads(filepath.read_text())
    if not data:
        return
    curated_keys: set[tuple[str | None, str | None]] = (
        await _curated_resource_keys(conn) if table == "resources" else set()
    )
    table_cols = ALLOWED_COLUMNS.get(table, set())
    for record in data:
        tagged = dict(record)
        if (
            city_slug is not None
            and "city" not in tagged
            and "city" in table_cols
        ):
            tagged["city"] = city_slug
        if table == "resources" and (
            (tagged.get("city"), tagged.get("name")) in curated_keys
        ):
            continue
        clean = validate_seed_record(table, tagged)
        if not clean:
            continue
        await _insert_seed_record(conn, table, clean)

"""Async SQLAlchemy database setup, supporting sqlite and postgres.

Heavy seeding helpers live in :mod:`app.core.seed_helpers` so this
module stays under the project's max-functions-per-file ceiling.  The
public entry points (``init_db``, ``seed_database``) stay here.

T22.2 wired in postgres support: the engine factory now dispatches
between ``sqlite+aiosqlite://`` and ``postgresql+asyncpg://`` URLs.
URL normalization + dialect detection live in :mod:`app.core.db_url`
so the runtime path mirrors ``backend/alembic/env.py``.
"""

import logging
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool, StaticPool

from app.cities.config import get_city_config
from app.core.config import get_settings
from app.core.db_url import is_sqlite_url, normalize_async_url
from app.core.schema import ALLOWED_COLUMNS, DDL_SQL
from app.core.seed_helpers import (
    apply_pending_migrations,
    city_resource_seed_files,  # noqa: F401 — re-exported for tests
    is_real_project_data_dir,
    resolve_seed_files,
    seed_from_file,
    seed_resources_all_cities,
    validate_seed_record as _validate_seed_record,  # legacy alias
)

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_DEFAULT_DATA_DIR = _PROJECT_ROOT / "data"


def resolve_data_dir() -> Path:
    """Return city-specific data directory, falling back to explicit DATA_DIR or default.

    Priority: city config data_dir (if it has seed files) > env DATA_DIR > default data/.
    """
    try:
        city = get_city_config()
        city_data = _PROJECT_ROOT / city.data_dir
        if city_data.is_dir() and any(city_data.glob("*.json")):
            return city_data.resolve()
    except Exception:
        pass  # Fall through to legacy resolution

    settings = get_settings()
    if settings.data_dir:
        return Path(settings.data_dir).resolve()
    return _DEFAULT_DATA_DIR


_engine = None
_async_session_factory = None


def get_engine():
    """Get or create the async engine.

    Dispatches by URL prefix:
    - sqlite (aiosqlite): uses ``StaticPool`` so a single connection
      is shared across the test/runtime process — required for
      in-memory SQLite and benign for file-based SQLite.
    - postgres (asyncpg): uses ``NullPool`` to mirror the
      Alembic env.py behaviour. Production deployments can switch
      to a real pool by overriding via env, but NullPool is the
      safe default — no dangling connections in CI.
    """
    global _engine
    if _engine is None:
        settings = get_settings()
        url = normalize_async_url(settings.database_url)
        poolclass = StaticPool if is_sqlite_url(url) else NullPool
        _engine = create_async_engine(
            url,
            echo=False,
            poolclass=poolclass,
        )
    return _engine


def get_async_session_factory() -> async_sessionmaker[AsyncSession]:
    """Get the async session factory."""
    global _async_session_factory
    if _async_session_factory is None:
        _async_session_factory = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _async_session_factory


async def get_db() -> AsyncSession:
    """Dependency for FastAPI routes to get a database session."""
    async_session = get_async_session_factory()
    async with async_session() as session:
        yield session


async def init_db(engine):
    """Create tables via raw DDL, apply pending migrations, then seed.

    The DDL_SQL block is the m001 baseline.  Every migration past m001
    (e.g. m008 ``resources.city``) is applied via the sync runner in a
    background thread so the runtime DB stays in lockstep with the
    test DB (which always uses ``apply_pending``).
    """
    async with engine.begin() as conn:
        for statement in DDL_SQL.strip().split(";"):
            statement = statement.strip()
            if statement:
                await conn.execute(text(statement))
    await apply_pending_migrations(engine)
    await seed_database(engine)


async def seed_database(engine):
    """Load city seed data (JSON) into SQLite on first run.

    Resources are seeded for EVERY configured city tagged with their
    slug, so per-request filtering can return only the active city's
    rows.  Other tables (employers, transit, jobs) keep the legacy
    single-city seed flow.
    """
    async with engine.begin() as conn:
        result = await conn.execute(text("SELECT COUNT(*) FROM resources"))
        if result.scalar() > 0:
            return

        data_dir = resolve_data_dir()
        if not data_dir.is_dir():
            logger.warning("DATA_DIR %s does not exist — skipping seed", data_dir)
            return

        # Resources first, multi-city.  Other tables stay city-specific.
        # When tests patch ``resolve_data_dir`` to an isolated directory
        # we honour the patch by skipping the multi-city scan; tests
        # that exercise the multi-city scan use the real data_dir.
        if is_real_project_data_dir(data_dir):
            await seed_resources_all_cities(conn)

        for filename, table in _seed_file_map():
            if filename == "resources.json" and is_real_project_data_dir(data_dir):
                continue  # already handled by seed_resources_all_cities
            filepaths = resolve_seed_files(data_dir, filename)
            if not filepaths:
                logger.warning("Seed file missing: %s", data_dir / filename)
                continue
            for filepath in filepaths:
                await seed_from_file(conn, filepath, table)


def _seed_file_map() -> list[tuple[str, str]]:
    """Return (filename, table) pairs for seeding.

    Uses city-agnostic filenames (employers.json, resources.json, etc.).
    Legacy Montgomery-specific filenames are resolved in seed_database
    via LEGACY_FALLBACKS when the generic file is not found.
    """
    return [
        ("employers.json", "employers"),
        ("resources.json", "resources"),
        ("transit_routes.json", "transit_routes"),
        ("transit_stops.json", "transit_stops"),
        ("job_listings.json", "job_listings"),
    ]


async def close_db() -> None:
    """Close the database engine."""
    global _engine, _async_session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _async_session_factory = None


# Re-exports for callers that import from app.core.database directly
# (test_database.py uses _validate_seed_record + ALLOWED_COLUMNS).
__all__ = [
    "ALLOWED_COLUMNS",
    "DDL_SQL",
    "_validate_seed_record",
    "close_db",
    "get_async_session_factory",
    "get_db",
    "get_engine",
    "init_db",
    "resolve_data_dir",
    "seed_database",
]

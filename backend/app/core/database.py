"""Async SQLAlchemy database setup for SQLite with raw DDL and seed data."""

import json
import logging
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.cities.config import get_city_config
from app.core.config import get_settings
from app.core.schema import ALLOWED_COLUMNS, DDL_SQL, JSON_FIELDS

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


def _validate_seed_record(table: str, record: dict) -> dict:
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

_engine = None
_async_session_factory = None


def get_engine():
    """Get or create the async engine."""
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.database_url,
            echo=False,
            poolclass=StaticPool,
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
    """Create tables via raw DDL, then seed with city data."""
    async with engine.begin() as conn:
        for statement in DDL_SQL.strip().split(";"):
            statement = statement.strip()
            if statement:
                await conn.execute(text(statement))
    await seed_database(engine)


async def seed_database(engine):
    """Load city seed data (JSON) into SQLite on first run."""
    async with engine.begin() as conn:
        result = await conn.execute(text("SELECT COUNT(*) FROM resources"))
        if result.scalar() > 0:
            return

        data_dir = resolve_data_dir()
        if not data_dir.is_dir():
            logger.warning("DATA_DIR %s does not exist — skipping seed", data_dir)
            return

        for filename, table in _seed_file_map():
            filepaths = _resolve_seed_files(data_dir, filename)
            if not filepaths:
                logger.warning("Seed file missing: %s", data_dir / filename)
                continue
            for filepath in filepaths:
                await _seed_from_file(conn, filepath, table)


def _resolve_seed_files(data_dir: Path, filename: str) -> list[Path]:
    """Resolve seed file path, trying legacy fallbacks if needed."""
    primary = data_dir / filename
    if primary.exists():
        return [primary]
    # Try legacy fallback files
    fallbacks = _LEGACY_FALLBACKS.get(filename, [])
    found = [data_dir / fb for fb in fallbacks if (data_dir / fb).exists()]
    return found


async def _seed_from_file(conn, filepath: Path, table: str) -> None:
    """Load a single seed file into the given table."""
    data = json.loads(filepath.read_text())
    if not data:
        return
    for record in data:
        clean = _validate_seed_record(table, record)
        if not clean:
            continue
        # SAFETY: table comes from _seed_file_map (hardcoded), columns from
        # _validate_seed_record (filtered against ALLOWED_COLUMNS allowlist).
        # Values are parameterized via :key binding. No user input reaches here.
        columns = ", ".join(clean.keys())
        placeholders = ", ".join(f":{k}" for k in clean.keys())
        await conn.execute(
            text(f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"),
            clean,
        )


_LEGACY_FALLBACKS: dict[str, list[str]] = {
    "employers.json": ["montgomery_businesses.json"],
    "resources.json": [
        "career_centers.json", "training_programs.json",
        "childcare_providers.json", "community_resources.json",
    ],
}


def _seed_file_map() -> list[tuple[str, str]]:
    """Return (filename, table) pairs for seeding.

    Uses city-agnostic filenames (employers.json, resources.json, etc.).
    Legacy Montgomery-specific filenames are resolved in seed_database
    via _LEGACY_FALLBACKS when the generic file is not found.
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

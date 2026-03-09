"""Async SQLAlchemy database setup for SQLite with raw DDL and seed data."""

import json
import logging
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.core.schema import ALLOWED_COLUMNS, DDL_SQL, JSON_FIELDS

logger = logging.getLogger(__name__)

_DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"


def resolve_data_dir() -> Path:
    """Return configured DATA_DIR or the default relative path."""
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
    """Create tables via raw DDL, then seed with Montgomery data."""
    async with engine.begin() as conn:
        for statement in DDL_SQL.strip().split(";"):
            statement = statement.strip()
            if statement:
                await conn.execute(text(statement))
    await seed_database(engine)


async def seed_database(engine):
    """Load Montgomery JSON data into SQLite on first run."""
    async with engine.begin() as conn:
        result = await conn.execute(text("SELECT COUNT(*) FROM resources"))
        if result.scalar() > 0:
            return

        data_dir = resolve_data_dir()
        if not data_dir.is_dir():
            logger.warning("DATA_DIR %s does not exist — skipping seed", data_dir)
            return

        for filename, table in _seed_file_map():
            filepath = data_dir / filename
            if not filepath.exists():
                logger.warning("Seed file missing: %s", filepath)
                continue
            data = json.loads(filepath.read_text())
            if not data:
                continue
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


def _seed_file_map():
    """Return (filename, table) pairs for seeding."""
    return [
        ("montgomery_businesses.json", "employers"),
        ("transit_routes.json", "transit_routes"),
        ("transit_stops.json", "transit_stops"),
        ("career_centers.json", "resources"),
        ("training_programs.json", "resources"),
        ("childcare_providers.json", "resources"),
        ("community_resources.json", "resources"),
        ("job_listings.json", "job_listings"),
    ]


async def close_db() -> None:
    """Close the database engine."""
    global _engine, _async_session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _async_session_factory = None

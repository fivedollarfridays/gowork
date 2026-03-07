"""Async SQLAlchemy database setup for SQLite with raw DDL and seed data."""

import json
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings

# From backend/app/core/database.py -> 4 parents up to project root
DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"

DDL_SQL = """
CREATE TABLE IF NOT EXISTS employers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    address TEXT,
    lat REAL,
    lng REAL,
    license_type TEXT,
    industry TEXT,
    active INTEGER DEFAULT 1
);
CREATE TABLE IF NOT EXISTS transit_routes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    route_number INTEGER NOT NULL,
    route_name TEXT NOT NULL,
    weekday_start TEXT,
    weekday_end TEXT,
    saturday INTEGER DEFAULT 1,
    sunday INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS transit_stops (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    route_id INTEGER REFERENCES transit_routes(id),
    stop_name TEXT NOT NULL,
    lat REAL NOT NULL,
    lng REAL NOT NULL,
    sequence INTEGER
);
CREATE TABLE IF NOT EXISTS resources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    subcategory TEXT,
    address TEXT,
    lat REAL,
    lng REAL,
    phone TEXT,
    url TEXT,
    eligibility TEXT,
    services TEXT,
    hours TEXT,
    notes TEXT,
    health_status TEXT DEFAULT 'healthy'
);
CREATE TABLE IF NOT EXISTS job_listings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    company TEXT,
    location TEXT,
    description TEXT,
    url TEXT,
    source TEXT,
    scraped_at TEXT NOT NULL,
    expires_at TEXT,
    credit_check TEXT DEFAULT 'unknown'
);
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    barriers TEXT NOT NULL,
    credit_profile TEXT,
    qualifications TEXT,
    plan TEXT,
    profile TEXT,
    expires_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS feedback_tokens (
    token TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS visit_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    submitted_at TEXT NOT NULL,
    made_it_to_center INTEGER NOT NULL,
    outcomes TEXT,
    plan_accuracy INTEGER NOT NULL,
    free_text TEXT,
    reviewed INTEGER DEFAULT 0,
    action_taken TEXT
);
CREATE TABLE IF NOT EXISTS resource_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    resource_id INTEGER REFERENCES resources(id),
    session_id TEXT NOT NULL,
    helpful INTEGER NOT NULL,
    barrier_type TEXT,
    submitted_at TEXT NOT NULL,
    UNIQUE(resource_id, session_id)
);
"""

ALLOWED_COLUMNS = {
    "employers": {"name", "address", "lat", "lng", "license_type", "industry", "active"},
    "transit_routes": {"route_number", "route_name", "weekday_start", "weekday_end", "saturday", "sunday"},
    "resources": {
        "name", "category", "subcategory", "address", "lat", "lng",
        "phone", "url", "eligibility", "services", "hours", "notes",
    },
    "job_listings": {
        "title", "company", "location", "description", "url",
        "source", "scraped_at", "expires_at", "credit_check",
    },
}

JSON_FIELDS = {"services"}


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

        for filename, table in _seed_file_map():
            filepath = DATA_DIR / filename
            if not filepath.exists():
                continue
            data = json.loads(filepath.read_text())
            if not data:
                continue
            for record in data:
                clean = _validate_seed_record(table, record)
                if not clean:
                    continue
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

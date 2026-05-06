"""Alembic env.py — async-aware, dispatches between sqlite and postgres.

Resolves DATABASE_URL from (in priority order):
  1. ``-x dburl=...`` Alembic CLI override
  2. ``DATABASE_URL`` environment variable
  3. ``app.core.config.Settings.database_url`` (default sqlite+aiosqlite)

The same env.py drives sqlite (aiosqlite) for local/dev/test and
postgres (asyncpg) for CI/production. Both use SQLAlchemy's async
engine; the URL prefix selects the driver. Postgres path is wired
here but not exercised until T22.2 lands asyncpg in requirements.txt.

Migration ordering convention is numeric (0001_, 0002_, ...) — see
script.py.mako.
"""

from __future__ import annotations

import asyncio
import os
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context

# Alembic Config object — provides access to alembic.ini values.
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Schema autogenerate target. Currently None because T22.1 only
# stands up the runner; T22.3 will port the m00X DDL into versioned
# migrations and wire SQLAlchemy models / metadata here.
target_metadata = None


def _resolve_database_url() -> str:
    """Resolve the DATABASE_URL from CLI, env, or app settings."""
    cli_args = context.get_x_argument(as_dictionary=True)
    if "dburl" in cli_args and cli_args["dburl"]:
        return cli_args["dburl"]
    env_url = os.environ.get("DATABASE_URL")
    if env_url:
        return env_url
    # Lazy import so importing env.py for offline mode without the
    # full app dependency tree (e.g. CI bootstrap) still works.
    from app.core.config import get_settings

    return get_settings().database_url


def _is_sqlite_url(url: str) -> bool:
    """Return True for sqlite URLs (sync or async drivers)."""
    return url.startswith("sqlite")


def _is_postgres_url(url: str) -> bool:
    """Return True for postgres URLs (sync or async drivers)."""
    return url.startswith("postgres") or url.startswith("postgresql")


def _normalize_async_url(url: str) -> str:
    """Coerce a sync URL into its async-driver equivalent.

    Lets callers pass either ``sqlite:///x`` or
    ``sqlite+aiosqlite:///x`` (likewise ``postgresql://`` →
    ``postgresql+asyncpg://``) — env.py always runs the async
    engine path, so we normalize once here.
    """
    if _is_sqlite_url(url) and "+aiosqlite" not in url:
        return url.replace("sqlite://", "sqlite+aiosqlite://", 1)
    if _is_postgres_url(url) and "+asyncpg" not in url and "+" not in url.split("://", 1)[0]:
        prefix, rest = url.split("://", 1)
        return f"{prefix}+asyncpg://{rest}"
    return url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (URL only, no DBAPI)."""
    url = _resolve_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def _do_run_migrations(connection: Connection) -> None:
    """Sync callback executed inside ``connection.run_sync``."""
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an async engine and run migrations through it.

    Works for both sqlite (aiosqlite) and postgres (asyncpg). Uses
    NullPool so the engine is fully torn down between alembic
    invocations — avoids dangling connections in CI.
    """
    url = _normalize_async_url(_resolve_database_url())
    connectable = create_async_engine(url, poolclass=pool.NullPool)
    async with connectable.connect() as connection:
        await connection.run_sync(_do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode via the async engine."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

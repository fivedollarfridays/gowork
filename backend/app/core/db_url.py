"""Database URL helpers shared between runtime engine + Alembic env.py.

T22.1 introduced async-aware URL handling in ``backend/alembic/env.py``.
T22.2 lifts that logic into a single module so the runtime engine in
``app.core.database`` and the migration runner in ``alembic/env.py``
both go through the same ``normalize_async_url`` + dialect detection,
keeping sqlite (aiosqlite) and postgres (asyncpg) wired identically.

Public API:
- ``is_sqlite_url(url)`` -> bool
- ``is_postgres_url(url)`` -> bool
- ``normalize_async_url(url)`` -> str  (coerce sync URLs to async drivers)
- ``infer_dialect(url)`` -> "sqlite" | "postgresql"
"""

from __future__ import annotations


def is_sqlite_url(url: str) -> bool:
    """Return True for sqlite URLs (sync or async drivers)."""
    return url.startswith("sqlite")


def is_postgres_url(url: str) -> bool:
    """Return True for postgres URLs (sync or async drivers)."""
    return url.startswith("postgres") or url.startswith("postgresql")


def normalize_async_url(url: str) -> str:
    """Coerce a sync URL into its async-driver equivalent.

    Lets callers pass either ``sqlite:///x`` or
    ``sqlite+aiosqlite:///x`` (likewise ``postgresql://`` →
    ``postgresql+asyncpg://``). If the URL already declares a driver
    (e.g. ``postgresql+psycopg://``) it is returned unchanged so an
    explicit driver choice is never clobbered.
    """
    if is_sqlite_url(url) and "+aiosqlite" not in url:
        return url.replace("sqlite://", "sqlite+aiosqlite://", 1)
    if is_postgres_url(url):
        prefix, rest = url.split("://", 1)
        # SQLAlchemy registers the dialect as ``postgresql``, not ``postgres``.
        # Heroku/Render/RDS commonly emit the short ``postgres://`` form, so
        # coerce to the canonical scheme before appending the async driver.
        if prefix in ("postgres", "postgres+asyncpg", "postgres+psycopg"):
            prefix = prefix.replace("postgres", "postgresql", 1)
        if "+" not in prefix:
            return f"{prefix}+asyncpg://{rest}"
        return f"{prefix}://{rest}"
    return url


def infer_dialect(url: str) -> str:
    """Return the SQLAlchemy dialect name for a database URL.

    Returns "sqlite" or "postgresql". Raises ``ValueError`` for any
    other scheme — we don't currently support mysql/oracle/mssql and
    silently defaulting would mask config typos.
    """
    if is_sqlite_url(url):
        return "sqlite"
    if is_postgres_url(url):
        return "postgresql"
    raise ValueError(f"Unsupported database URL scheme: {url!r}")

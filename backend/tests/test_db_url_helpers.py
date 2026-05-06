"""Tests for app.core.db_url URL normalization + dialect inference helpers.

These helpers back both `app.core.database` (runtime engine creation) and
`alembic/env.py` (migration runner). T22.2 introduced them to avoid
duplicating sqlite/postgres URL handling across the two callsites.
"""

import pytest

from app.core.db_url import (
    infer_dialect,
    is_postgres_url,
    is_sqlite_url,
    normalize_async_url,
)


class TestIsSqliteUrl:
    def test_aiosqlite_recognized(self):
        assert is_sqlite_url("sqlite+aiosqlite:///./montgowork.db") is True

    def test_plain_sqlite_recognized(self):
        assert is_sqlite_url("sqlite:///./montgowork.db") is True

    def test_postgres_not_sqlite(self):
        assert is_sqlite_url("postgresql+asyncpg://u:p@h/d") is False


class TestIsPostgresUrl:
    def test_postgresql_async_recognized(self):
        assert is_postgres_url("postgresql+asyncpg://u:p@h/d") is True

    def test_postgres_short_recognized(self):
        assert is_postgres_url("postgres://u:p@h/d") is True

    def test_sqlite_not_postgres(self):
        assert is_postgres_url("sqlite+aiosqlite:///x") is False


class TestNormalizeAsyncUrl:
    def test_sqlite_sync_to_aiosqlite(self):
        assert (
            normalize_async_url("sqlite:///./db.sqlite")
            == "sqlite+aiosqlite:///./db.sqlite"
        )

    def test_sqlite_already_async_passthrough(self):
        url = "sqlite+aiosqlite:///./db.sqlite"
        assert normalize_async_url(url) == url

    def test_postgres_sync_to_asyncpg(self):
        assert (
            normalize_async_url("postgresql://u:p@h/d")
            == "postgresql+asyncpg://u:p@h/d"
        )

    def test_postgres_already_async_passthrough(self):
        url = "postgresql+asyncpg://u:p@h/d"
        assert normalize_async_url(url) == url

    def test_postgres_with_psycopg_driver_passthrough(self):
        # Don't clobber an explicit non-asyncpg driver choice.
        url = "postgresql+psycopg://u:p@h/d"
        assert normalize_async_url(url) == url


class TestInferDialect:
    def test_sqlite_url_yields_sqlite(self):
        assert infer_dialect("sqlite+aiosqlite:///./x.db") == "sqlite"

    def test_postgres_url_yields_postgres(self):
        assert infer_dialect("postgresql+asyncpg://u:p@h/d") == "postgresql"

    def test_postgres_short_yields_postgres(self):
        assert infer_dialect("postgres://u:p@h/d") == "postgresql"

    def test_unknown_url_raises(self):
        with pytest.raises(ValueError):
            infer_dialect("mysql://u:p@h/d")

"""Tests for ``app.core.database.get_engine`` dual-driver dispatch.

T22.2 made the runtime engine factory aware of both sqlite and postgres
URLs. The engine config — pool class, normalization — depends on the
URL prefix. These tests exercise the dispatch without standing up a
real postgres instance: we only assert on the engine object's URL +
pool class.
"""

import pytest

from app.core import database as db_module
from app.core.config import get_settings


@pytest.fixture(autouse=True)
def _reset_engine_globals():
    """Each test starts from a clean engine factory."""
    old_engine = db_module._engine
    old_factory = db_module._async_session_factory
    db_module._engine = None
    db_module._async_session_factory = None
    get_settings.cache_clear()
    yield
    db_module._engine = old_engine
    db_module._async_session_factory = old_factory
    get_settings.cache_clear()


class TestSqliteEngine:
    def test_sqlite_default_url_creates_engine(self):
        engine = db_module.get_engine()
        assert engine.url.drivername == "sqlite+aiosqlite"


class TestPostgresEngine:
    def test_postgres_url_creates_asyncpg_engine(self, monkeypatch):
        monkeypatch.setenv(
            "DATABASE_URL", "postgresql+asyncpg://u:p@127.0.0.1/d"
        )
        get_settings.cache_clear()
        engine = db_module.get_engine()
        assert engine.url.drivername == "postgresql+asyncpg"

    def test_postgres_sync_url_normalized_to_asyncpg(self, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@127.0.0.1/d")
        get_settings.cache_clear()
        engine = db_module.get_engine()
        assert engine.url.drivername == "postgresql+asyncpg"

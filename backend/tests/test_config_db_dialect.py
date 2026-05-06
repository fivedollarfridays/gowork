"""Tests for the ``Settings.db_dialect`` property added in T22.2.

The property is the single source of truth for "which engine are we
talking to?" — used by app.core.database for pool selection and by
test fixtures to skip postgres-specific paths when only sqlite is
configured.
"""

import pytest

from app.core.config import Settings


class TestDbDialect:
    def test_sqlite_default(self):
        settings = Settings()
        assert settings.db_dialect == "sqlite"

    def test_postgres_url_yields_postgresql(self, monkeypatch):
        monkeypatch.setenv(
            "DATABASE_URL", "postgresql+asyncpg://u:p@localhost/d"
        )
        settings = Settings()
        assert settings.db_dialect == "postgresql"

    def test_unsupported_url_raises_at_access(self, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", "mysql://u:p@h/d")
        # The validator runs at instantiation — Pydantic surfaces it
        # as a ValidationError, but the underlying cause is ValueError
        # from infer_dialect.
        with pytest.raises(Exception) as excinfo:
            Settings()
        assert "Unsupported" in str(excinfo.value) or "mysql" in str(excinfo.value)

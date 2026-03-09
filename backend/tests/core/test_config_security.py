"""Tests for production security validators in Settings."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.config import Settings, get_settings

_SAFE_SALT = "a-real-production-salt-value-here"
_SAFE_ADMIN_KEY = "x" * 32
_DEFAULT_SALT = "montgowork-default-salt"
_SHORT_KEY = "x" * 7  # under 32 chars, triggers validator
_TEST_KEY = "t" * 8  # non-production test key
_PROD_CORS = "https://app.montgowork.org"


class TestAuditHashSaltValidator:
    """HIGH-3 / LOW-4: Reject weak default audit hash salt in production."""

    def setup_method(self):
        get_settings.cache_clear()

    def test_rejects_default_salt_in_production(self):
        """Production must not use the hardcoded default salt."""
        with pytest.raises(ValueError, match="audit_hash_salt"):
            Settings(
                environment="production",
                audit_hash_salt="montgowork-default-salt",
                credit_api_url="https://credit.example.com",
                cors_origins=_PROD_CORS,
            )

    def test_rejects_default_salt_explicitly_in_production(self):
        """Production with the default salt value must fail."""
        with pytest.raises(ValueError, match="audit_hash_salt"):
            Settings(
                environment="production",
                audit_hash_salt=_DEFAULT_SALT,
                credit_api_url="https://credit.example.com",
                cors_origins=_PROD_CORS,
            )

    def test_accepts_custom_salt_in_production(self):
        """Production with a custom salt should pass."""
        s = Settings(
            environment="production",
            audit_hash_salt=_SAFE_SALT,
            admin_api_key=_SAFE_ADMIN_KEY,
            credit_api_url="https://credit.example.com",
            cors_origins=_PROD_CORS,
        )
        assert s.audit_hash_salt == _SAFE_SALT

    def test_warns_default_salt_in_staging(self):
        """Staging with default salt should log a warning but not error."""
        import logging
        with patch.object(logging.getLogger("app.core.config"), "warning") as mock_warn:
            s = Settings(environment="staging", audit_hash_salt=_DEFAULT_SALT)
            assert s.audit_hash_salt == _DEFAULT_SALT
            mock_warn.assert_called_once()
            assert "audit_hash_salt" in str(mock_warn.call_args)

    def test_allows_default_salt_in_development(self):
        """Development can use the default salt without error."""
        s = Settings(environment="development", audit_hash_salt=_DEFAULT_SALT)
        assert s.audit_hash_salt == _DEFAULT_SALT

    def test_allows_default_salt_in_test(self):
        """Test environment can use the default salt without error."""
        s = Settings(environment="test", audit_hash_salt=_DEFAULT_SALT)
        assert s.audit_hash_salt == _DEFAULT_SALT


class TestAdminApiKeyValidator:
    """MED-6: Reject weak admin key in production."""

    def setup_method(self):
        get_settings.cache_clear()

    def test_rejects_short_admin_key_in_production(self):
        """Production admin_api_key must be >= 32 characters."""
        with pytest.raises(ValueError, match="admin_api_key"):
            Settings(
                environment="production",
                admin_api_key=_SHORT_KEY,
                audit_hash_salt=_SAFE_SALT,
                credit_api_url="https://credit.example.com",
                cors_origins=_PROD_CORS,
            )

    def test_rejects_empty_admin_key_in_production(self):
        """Production with empty admin_api_key must fail."""
        with pytest.raises(ValueError, match="admin_api_key"):
            Settings(
                environment="production",
                admin_api_key="",
                audit_hash_salt=_SAFE_SALT,
                credit_api_url="https://credit.example.com",
                cors_origins=_PROD_CORS,
            )

    def test_accepts_long_admin_key_in_production(self):
        """Production with a 32+ char admin key should pass."""
        s = Settings(
            environment="production",
            admin_api_key=_SAFE_ADMIN_KEY,
            audit_hash_salt=_SAFE_SALT,
            credit_api_url="https://credit.example.com",
            cors_origins=_PROD_CORS,
        )
        assert s.admin_api_key == _SAFE_ADMIN_KEY

    def test_allows_empty_admin_key_in_development(self):
        """Development can use empty admin key."""
        s = Settings(environment="development", admin_api_key="")
        assert s.admin_api_key == ""

    def test_allows_short_admin_key_in_development(self):
        """Development can use a short admin key."""
        s = Settings(environment="development", admin_api_key="dev-key")
        assert s.admin_api_key == "dev-key"

    def test_allows_short_admin_key_in_test(self):
        """Test environment can use a short admin key."""
        s = Settings(environment="test", admin_api_key=_TEST_KEY)
        assert s.admin_api_key == _TEST_KEY


class TestCorsLocalhostValidator:
    """Reject localhost CORS origins in production."""

    def setup_method(self):
        get_settings.cache_clear()

    def test_rejects_localhost_cors_in_production(self):
        with pytest.raises(ValueError, match="cors_origins"):
            Settings(
                environment="production",
                audit_hash_salt=_SAFE_SALT,
                admin_api_key=_SAFE_ADMIN_KEY,
                credit_api_url="https://credit.example.com",
                cors_origins="http://localhost:3000",
            )

    def test_accepts_production_cors_origins(self):
        s = Settings(
            environment="production",
            audit_hash_salt=_SAFE_SALT,
            admin_api_key=_SAFE_ADMIN_KEY,
            credit_api_url="https://credit.example.com",
            cors_origins=_PROD_CORS,
        )
        assert "localhost" not in s.cors_origins

    def test_allows_localhost_cors_in_development(self):
        s = Settings(environment="development", cors_origins="http://localhost:3000")
        assert "localhost" in s.cors_origins


_MOCK_SEEDS = "app.core.startup.run_seeds_and_rag"


class TestStartupEnvironmentWarning:
    """LOW-1: Warn on startup if ENVIRONMENT is not explicitly set."""

    @pytest.mark.anyio
    async def test_warns_when_environment_defaults_to_development(self):
        """Startup should log a warning when ENVIRONMENT env var is not set."""
        import os
        from app.main import lifespan, app

        mock_engine = AsyncMock()
        mock_status = {
            "providers": {"mock": "available"},
            "active": "mock",
        }
        # Build env dict without ENVIRONMENT key
        clean_env = {k: v for k, v in os.environ.items() if k != "ENVIRONMENT"}
        with patch("app.main.get_engine", return_value=mock_engine), \
             patch("app.main.init_db", new_callable=AsyncMock), \
             patch("app.main.close_db", new_callable=AsyncMock), \
             patch(_MOCK_SEEDS, new_callable=AsyncMock, return_value=MagicMock()), \
             patch("app.main.check_llm_providers", return_value=mock_status), \
             patch("app.main.logger") as mock_logger, \
             patch.dict("os.environ", clean_env, clear=True):
            async with lifespan(app):
                pass
        warning_calls = [str(c) for c in mock_logger.warning.call_args_list]
        assert any("ENVIRONMENT" in c for c in warning_calls)

    @pytest.mark.anyio
    async def test_no_env_warning_when_environment_is_set(self):
        """No warning when ENVIRONMENT env var is explicitly set."""
        from app.main import lifespan, app

        mock_engine = AsyncMock()
        mock_status = {
            "providers": {"mock": "available"},
            "active": "mock",
        }
        with patch("app.main.get_engine", return_value=mock_engine), \
             patch("app.main.init_db", new_callable=AsyncMock), \
             patch("app.main.close_db", new_callable=AsyncMock), \
             patch(_MOCK_SEEDS, new_callable=AsyncMock, return_value=MagicMock()), \
             patch("app.main.check_llm_providers", return_value=mock_status), \
             patch("app.main.logger") as mock_logger, \
             patch.dict("os.environ", {"ENVIRONMENT": "staging"}, clear=False):
            async with lifespan(app):
                pass
        warning_calls = [str(c) for c in mock_logger.warning.call_args_list]
        assert not any("ENVIRONMENT" in c for c in warning_calls)

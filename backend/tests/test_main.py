"""Tests for app entry point — root endpoint and lifespan."""

import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware


def _mock_rag_store():
    """Return a patch that replaces RagStore with a no-op mock."""
    mock_store = MagicMock()
    mock_store.build_or_load = AsyncMock()
    return patch("app.main.RagStore", return_value=mock_store)


class TestSwaggerDocs:
    @pytest.mark.anyio
    async def test_docs_available_in_development(self, client):
        """Swagger UI is served in development mode."""
        resp = await client.get("/docs")
        assert resp.status_code == 200

    def test_docs_url_set_in_development(self):
        """App has docs_url set when not in production."""
        from app.main import app
        assert app.docs_url == "/docs"


class TestRootEndpoint:
    @pytest.mark.anyio
    async def test_returns_status(self, client):
        resp = await client.get("/")
        assert resp.status_code == 200
        body = resp.json()
        assert body["message"] == "MontGoWork API"
        assert body["status"] == "running"


class TestProxyHeadersMiddleware:
    def test_proxy_headers_middleware_registered(self):
        """ProxyHeadersMiddleware is in the middleware stack."""
        from app.main import app

        middleware_classes = [m.cls for m in app.user_middleware]
        assert ProxyHeadersMiddleware in middleware_classes

    def test_trusted_hosts_defaults_to_localhost(self):
        """Default trusted_hosts is localhost only (safe default)."""
        from app.core.config import Settings

        s = Settings(cors_origins="http://localhost:3000")
        assert s.trusted_proxy_hosts == "127.0.0.1"

    def test_trusted_hosts_configurable(self):
        """trusted_proxy_hosts is configurable via settings."""
        from app.core.config import Settings

        s = Settings(cors_origins="http://localhost:3000", trusted_proxy_hosts="10.0.0.0/8,172.16.0.0/12")
        assert "10.0.0.0/8" in s.trusted_proxy_hosts
        assert "172.16.0.0/12" in s.trusted_proxy_hosts


class TestLifespan:
    @pytest.mark.anyio
    async def test_startup_and_shutdown(self):
        from app.main import lifespan, app

        mock_engine = AsyncMock()
        with patch("app.main.get_engine", return_value=mock_engine) as mock_ge, \
             patch("app.main.init_db", new_callable=AsyncMock) as mock_init, \
             patch("app.main.close_db", new_callable=AsyncMock) as mock_close, \
             patch("app.main.upsert_barrier_graph", new_callable=AsyncMock), \
             patch("app.main.seed_employer_policies", new_callable=AsyncMock), \
             _mock_rag_store():
            async with lifespan(app):
                mock_ge.assert_called_once()
                mock_init.assert_awaited_once_with(mock_engine)
            mock_close.assert_awaited_once()

    @pytest.mark.anyio
    async def test_shutdown_disposes_engine(self):
        """close_db is called on shutdown to dispose the engine."""
        from app.main import lifespan, app

        mock_engine = AsyncMock()
        with patch("app.main.get_engine", return_value=mock_engine), \
             patch("app.main.init_db", new_callable=AsyncMock), \
             patch("app.main.close_db", new_callable=AsyncMock) as mock_close, \
             patch("app.main.upsert_barrier_graph", new_callable=AsyncMock), \
             patch("app.main.seed_employer_policies", new_callable=AsyncMock), \
             _mock_rag_store():
            async with lifespan(app):
                pass
            mock_close.assert_awaited_once()

    @pytest.mark.anyio
    async def test_warns_when_web_concurrency_gt_1(self):
        """Startup should log a warning when WEB_CONCURRENCY > 1."""
        from app.main import lifespan, app

        mock_engine = AsyncMock()
        with patch("app.main.get_engine", return_value=mock_engine), \
             patch("app.main.init_db", new_callable=AsyncMock), \
             patch("app.main.close_db", new_callable=AsyncMock), \
             patch("app.main.upsert_barrier_graph", new_callable=AsyncMock), \
             patch("app.main.seed_employer_policies", new_callable=AsyncMock), \
             _mock_rag_store(), \
             patch("app.main.logger") as mock_logger, \
             patch.dict("os.environ", {"WEB_CONCURRENCY": "4"}):
            async with lifespan(app):
                pass
        warning_calls = [
            str(c) for c in mock_logger.warning.call_args_list
        ]
        assert any("WEB_CONCURRENCY" in c for c in warning_calls)
        assert any("rate limit" in c.lower() for c in warning_calls)

    @pytest.mark.anyio
    async def test_no_warning_when_web_concurrency_is_1(self):
        """No warning when WEB_CONCURRENCY is 1."""
        from app.main import lifespan, app

        mock_engine = AsyncMock()
        with patch("app.main.get_engine", return_value=mock_engine), \
             patch("app.main.init_db", new_callable=AsyncMock), \
             patch("app.main.close_db", new_callable=AsyncMock), \
             patch("app.main.upsert_barrier_graph", new_callable=AsyncMock), \
             patch("app.main.seed_employer_policies", new_callable=AsyncMock), \
             _mock_rag_store(), \
             patch("app.main.logger") as mock_logger, \
             patch.dict("os.environ", {"WEB_CONCURRENCY": "1"}):
            async with lifespan(app):
                pass
        warning_calls = [
            str(c) for c in mock_logger.warning.call_args_list
        ]
        assert not any("WEB_CONCURRENCY" in c for c in warning_calls)

    @pytest.mark.anyio
    async def test_logs_llm_provider_status_on_startup(self):
        """Lifespan logs LLM provider status during startup."""
        from app.main import lifespan, app

        mock_engine = AsyncMock()
        mock_status = {
            "providers": {"anthropic": "configured", "openai": "no_key", "gemini": "no_key", "mock": "available"},
            "active": "anthropic",
        }
        with patch("app.main.get_engine", return_value=mock_engine), \
             patch("app.main.init_db", new_callable=AsyncMock), \
             patch("app.main.close_db", new_callable=AsyncMock), \
             patch("app.main.upsert_barrier_graph", new_callable=AsyncMock), \
             patch("app.main.seed_employer_policies", new_callable=AsyncMock), \
             _mock_rag_store(), \
             patch("app.main.check_llm_providers", return_value=mock_status), \
             patch("app.main.logger") as mock_logger:
            async with lifespan(app):
                pass
        info_calls = [str(c) for c in mock_logger.info.call_args_list]
        assert any("LLM" in c and "anthropic" in c for c in info_calls)

    @pytest.mark.anyio
    async def test_warns_when_llm_falls_back_to_mock(self):
        """Lifespan warns when no LLM provider configured (mock fallback)."""
        from app.main import lifespan, app

        mock_engine = AsyncMock()
        mock_status = {
            "providers": {"anthropic": "no_key", "openai": "no_key", "gemini": "no_key", "mock": "available"},
            "active": "mock",
        }
        with patch("app.main.get_engine", return_value=mock_engine), \
             patch("app.main.init_db", new_callable=AsyncMock), \
             patch("app.main.close_db", new_callable=AsyncMock), \
             patch("app.main.upsert_barrier_graph", new_callable=AsyncMock), \
             patch("app.main.seed_employer_policies", new_callable=AsyncMock), \
             _mock_rag_store(), \
             patch("app.main.check_llm_providers", return_value=mock_status), \
             patch("app.main.logger") as mock_logger:
            async with lifespan(app):
                pass
        warning_calls = [str(c) for c in mock_logger.warning.call_args_list]
        assert any("mock" in c.lower() for c in warning_calls)

    @pytest.mark.anyio
    async def test_app_starts_with_no_providers(self):
        """App starts gracefully even with no LLM providers available."""
        from app.main import lifespan, app

        mock_engine = AsyncMock()
        mock_status = {
            "providers": {"anthropic": "no_key", "openai": "no_key", "gemini": "no_key", "mock": "available"},
            "active": "mock",
        }
        with patch("app.main.get_engine", return_value=mock_engine), \
             patch("app.main.init_db", new_callable=AsyncMock), \
             patch("app.main.close_db", new_callable=AsyncMock), \
             patch("app.main.upsert_barrier_graph", new_callable=AsyncMock), \
             patch("app.main.seed_employer_policies", new_callable=AsyncMock), \
             _mock_rag_store(), \
             patch("app.main.check_llm_providers", return_value=mock_status):
            async with lifespan(app):
                pass

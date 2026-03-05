"""Tests for app entry point — root endpoint and lifespan."""

from unittest.mock import AsyncMock, patch

import pytest


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


class TestLifespan:
    @pytest.mark.anyio
    async def test_startup_and_shutdown(self):
        from app.main import lifespan, app

        mock_engine = AsyncMock()
        with patch("app.main.get_engine", return_value=mock_engine) as mock_ge, \
             patch("app.main.init_db", new_callable=AsyncMock) as mock_init, \
             patch("app.main.close_db", new_callable=AsyncMock) as mock_close:
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
             patch("app.main.close_db", new_callable=AsyncMock) as mock_close:
            async with lifespan(app):
                pass
            mock_close.assert_awaited_once()

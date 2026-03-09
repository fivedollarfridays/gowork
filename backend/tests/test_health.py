"""Tests for health check endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.health.checks import check_database, check_rag_store
from app.health.models import ServiceCheck


class TestCheckDatabase:
    @pytest.mark.anyio
    async def test_success_returns_up(self):
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock()

        mock_engine = MagicMock()
        mock_engine.connect = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_conn),
            __aexit__=AsyncMock(return_value=False),
        ))

        with patch("app.health.checks.get_engine", return_value=mock_engine):
            result = await check_database()
        assert result.status == "up"
        assert result.name == "database"
        assert result.latency_ms is not None

    @pytest.mark.anyio
    async def test_failure_returns_down(self):
        with patch("app.health.checks.get_engine", side_effect=RuntimeError("no db")):
            result = await check_database()
        assert result.status == "down"
        assert result.error == "no db"


class TestCheckRagStore:
    def _make_request(self, rag_store=None, *, omit_attr: bool = False):
        """Build a mock Request with optional rag_store on app.state."""
        state = MagicMock()
        if omit_attr:
            del state.rag_store  # getattr will return None
        else:
            state.rag_store = rag_store
        app = MagicMock()
        app.state = state
        request = MagicMock()
        request.app = app
        return request

    def test_rag_store_none_returns_down(self):
        """store is None -> status down, error 'Not initialized'."""
        request = self._make_request(omit_attr=True)
        result = check_rag_store(request)
        assert result.status == "down"
        assert result.error == "Not initialized"
        assert result.name == "rag_store"

    def test_rag_store_ready_returns_up(self):
        """store.is_ready() True -> status up."""
        store = MagicMock()
        store.is_ready.return_value = True
        request = self._make_request(rag_store=store)
        result = check_rag_store(request)
        assert result.status == "up"
        assert result.latency_ms == 0

    def test_rag_store_not_ready_returns_down(self):
        """store.is_ready() False -> status down, 'Index not loaded'."""
        store = MagicMock()
        store.is_ready.return_value = False
        request = self._make_request(rag_store=store)
        result = check_rag_store(request)
        assert result.status == "down"
        assert result.error == "Index not loaded"

    def test_rag_store_exception_returns_down(self):
        """store.is_ready() raises -> status down with error message."""
        store = MagicMock()
        store.is_ready.side_effect = RuntimeError("boom")
        request = self._make_request(rag_store=store)
        result = check_rag_store(request)
        assert result.status == "down"
        assert result.error == "boom"


class TestLiveness:
    @pytest.mark.anyio
    async def test_returns_alive(self, client):
        resp = await client.get("/health/live")
        assert resp.status_code == 200
        body = resp.json()
        assert body["alive"] is True
        assert body["uptime_seconds"] >= 0


class TestReadiness:
    @pytest.mark.anyio
    async def test_ready_when_db_up(self, client):
        up_check = ServiceCheck(name="database", status="up", latency_ms=1.0)
        rag_check = ServiceCheck(name="rag_store", status="up", latency_ms=0)
        with patch("app.health.checks.check_database", return_value=up_check), \
             patch("app.health.checks.check_rag_store", return_value=rag_check):
            resp = await client.get("/health/ready")
        assert resp.status_code == 200
        assert resp.json()["ready"] is True

    @pytest.mark.anyio
    async def test_not_ready_when_db_down(self, client):
        down_check = ServiceCheck(name="database", status="down", error="fail")
        rag_check = ServiceCheck(name="rag_store", status="up", latency_ms=0)
        with patch("app.health.checks.check_database", return_value=down_check), \
             patch("app.health.checks.check_rag_store", return_value=rag_check):
            resp = await client.get("/health/ready")
        assert resp.status_code == 503
        assert resp.json()["ready"] is False


class TestHealth:
    @pytest.mark.anyio
    async def test_healthy_when_db_up(self, client):
        up_check = MagicMock(status="up")
        with patch("app.health.checks.check_database", return_value=up_check):
            resp = await client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "healthy"
        assert body["version"] == "0.1.0"

    @pytest.mark.anyio
    async def test_degraded_when_db_down(self, client):
        down_check = MagicMock(status="down")
        with patch("app.health.checks.check_database", return_value=down_check):
            resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "degraded"

    @pytest.mark.anyio
    async def test_unhealthy_when_check_raises(self, client):
        with patch("app.health.checks.check_database", side_effect=RuntimeError("crash")):
            resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "unhealthy"

    @pytest.mark.anyio
    async def test_includes_llm_provider(self, client):
        """Health endpoint reports active LLM provider."""
        from app.main import app
        up_check = MagicMock(status="up")
        mock_status = {"providers": {"anthropic": "configured"}, "active": "anthropic"}
        with patch("app.health.checks.check_database", return_value=up_check), \
             patch("app.health.checks.get_llm_status", return_value=mock_status):
            resp = await client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["llm_provider"] == "anthropic"

    @pytest.mark.anyio
    async def test_llm_provider_mock_when_no_keys(self, client):
        """Health endpoint shows mock when no LLM keys configured."""
        from app.main import app
        up_check = MagicMock(status="up")
        mock_status = {"providers": {"anthropic": "no_key"}, "active": "mock"}
        with patch("app.health.checks.check_database", return_value=up_check), \
             patch("app.health.checks.get_llm_status", return_value=mock_status):
            resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["llm_provider"] == "mock"

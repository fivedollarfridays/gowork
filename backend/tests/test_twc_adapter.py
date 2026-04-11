"""Tests for TWCJobAdapter — stub adapter returning [] with one-time log."""

import logging

import pytest


class TestTWCAdapterFetchJobs:
    @pytest.mark.anyio
    async def test_returns_empty_list(self):
        from app.integrations.adapters.twc_adapter import TWCJobAdapter

        adapter = TWCJobAdapter()
        result = await adapter.fetch_jobs(None, "jobs", "Fort Worth, TX")
        assert result == []

    @pytest.mark.anyio
    async def test_returns_list_type(self):
        from app.integrations.adapters.twc_adapter import TWCJobAdapter

        adapter = TWCJobAdapter()
        result = await adapter.fetch_jobs(None, "warehouse", "Dallas, TX")
        assert isinstance(result, list)

    @pytest.mark.anyio
    async def test_multiple_calls_return_empty(self):
        from app.integrations.adapters.twc_adapter import TWCJobAdapter

        adapter = TWCJobAdapter()
        for _ in range(3):
            result = await adapter.fetch_jobs(None, "any", "anywhere")
            assert result == []


class TestTWCAdapterProtocol:
    def test_satisfies_job_adapter_protocol(self):
        from app.integrations.adapters.base import JobAdapter
        from app.integrations.adapters.twc_adapter import TWCJobAdapter

        assert isinstance(TWCJobAdapter(), JobAdapter)

    def test_registry_returns_adapter(self):
        from app.integrations.adapters.base import get_adapter, JobAdapter

        adapter = get_adapter("twc")
        assert isinstance(adapter, JobAdapter)


class TestTWCAdapterLogging:
    def test_logs_stub_warning_once(self, caplog):
        import importlib
        import app.integrations.adapters.twc_adapter as mod

        mod._stub_logged = False
        importlib.reload(mod)

        warnings = [
            r for r in caplog.records
            if r.levelno == logging.WARNING and "twc" in r.message.lower()
        ]
        assert len(warnings) == 1
        assert "S2" in warnings[0].message or "s2" in warnings[0].message.lower()

    @pytest.mark.anyio
    async def test_no_log_on_fetch(self, caplog):
        from app.integrations.adapters.twc_adapter import TWCJobAdapter

        caplog.clear()
        adapter = TWCJobAdapter()
        with caplog.at_level(logging.WARNING):
            await adapter.fetch_jobs(None, "jobs", "Fort Worth, TX")
            await adapter.fetch_jobs(None, "jobs", "Fort Worth, TX")

        fetch_warnings = [
            r for r in caplog.records
            if r.levelno == logging.WARNING and "twc" in r.message.lower()
        ]
        assert len(fetch_warnings) == 0

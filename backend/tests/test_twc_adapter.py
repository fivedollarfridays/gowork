"""Tests for TWCJobAdapter -- live adapter with graceful degradation."""

import logging
from unittest.mock import AsyncMock, patch

import pytest


class TestTWCAdapterFetchJobs:
    @pytest.mark.anyio
    async def test_returns_list_type(self):
        from app.integrations.adapters.twc_adapter import TWCJobAdapter

        adapter = TWCJobAdapter()
        with patch("app.integrations.adapters.twc_adapter._fetch_twc_jobs", return_value=[]):
            result = await adapter.fetch_jobs(None, "warehouse", "Fort Worth, TX")
            assert isinstance(result, list)

    @pytest.mark.anyio
    async def test_degrades_gracefully_on_error(self):
        from app.integrations.adapters.twc_adapter import TWCJobAdapter

        adapter = TWCJobAdapter()
        with patch("app.integrations.adapters.twc_adapter._fetch_twc_jobs", side_effect=Exception("API down")):
            result = await adapter.fetch_jobs(None, "jobs", "Fort Worth, TX")
            assert result == []

    @pytest.mark.anyio
    async def test_returns_normalized_results(self):
        from app.integrations.adapters.twc_adapter import TWCJobAdapter

        mock_jobs = [{"title": "Driver", "company": "Co", "location": "FW", "url": "http://x", "source": "twc", "fair_chance": 0}]
        adapter = TWCJobAdapter()
        with patch("app.integrations.adapters.twc_adapter._fetch_twc_jobs", return_value=mock_jobs):
            result = await adapter.fetch_jobs(None, "driver", "Fort Worth, TX")
            assert len(result) == 1
            assert result[0]["source"] == "twc"


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
    @pytest.mark.anyio
    async def test_logs_warning_on_api_failure(self, caplog):
        from app.integrations.adapters.twc_adapter import TWCJobAdapter

        adapter = TWCJobAdapter()
        with caplog.at_level(logging.WARNING):
            with patch("app.integrations.adapters.twc_adapter._fetch_twc_jobs", side_effect=Exception("timeout")):
                await adapter.fetch_jobs(None, "jobs", "Fort Worth, TX")

        warnings = [r for r in caplog.records if r.levelno == logging.WARNING and "twc" in r.message.lower()]
        assert len(warnings) >= 1

    def test_no_log_at_import_time(self, caplog):
        import importlib
        import app.integrations.adapters.twc_adapter as mod

        caplog.clear()
        with caplog.at_level(logging.WARNING):
            importlib.reload(mod)
        import_warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert len(import_warnings) == 0

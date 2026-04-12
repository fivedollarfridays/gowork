"""Tests for USAJobsJobAdapter -- live adapter with graceful degradation."""

import logging
from unittest.mock import patch

import pytest


class TestUSAJobsAdapterFetchJobs:
    @pytest.mark.anyio
    async def test_returns_empty_list_without_api_key(self):
        from app.integrations.adapters.usajobs_adapter import USAJobsJobAdapter

        adapter = USAJobsJobAdapter()
        with patch("app.integrations.adapters.usajobs_adapter._get_api_key", return_value=""):
            result = await adapter.fetch_jobs(None, "jobs", "Fort Worth, TX")
            assert result == []

    @pytest.mark.anyio
    async def test_returns_list_type(self):
        from app.integrations.adapters.usajobs_adapter import USAJobsJobAdapter

        adapter = USAJobsJobAdapter()
        with patch("app.integrations.adapters.usajobs_adapter._get_api_key", return_value=""):
            result = await adapter.fetch_jobs(None, "federal", "DC")
            assert isinstance(result, list)

    @pytest.mark.anyio
    async def test_degrades_gracefully_on_error(self):
        from app.integrations.adapters.usajobs_adapter import USAJobsJobAdapter

        adapter = USAJobsJobAdapter()
        with patch("app.integrations.adapters.usajobs_adapter._get_api_key", return_value="test-key"), \
             patch("app.integrations.adapters.usajobs_adapter._fetch_usajobs", side_effect=Exception("API error")):
            result = await adapter.fetch_jobs(None, "any", "anywhere")
            assert result == []


class TestUSAJobsAdapterProtocol:
    def test_satisfies_job_adapter_protocol(self):
        from app.integrations.adapters.base import JobAdapter
        from app.integrations.adapters.usajobs_adapter import USAJobsJobAdapter

        assert isinstance(USAJobsJobAdapter(), JobAdapter)

    def test_registry_returns_adapter(self):
        from app.integrations.adapters.base import get_adapter, JobAdapter

        adapter = get_adapter("usajobs")
        assert isinstance(adapter, JobAdapter)


class TestUSAJobsAdapterLogging:
    @pytest.mark.anyio
    async def test_logs_warning_on_api_failure(self, caplog):
        from app.integrations.adapters.usajobs_adapter import USAJobsJobAdapter

        adapter = USAJobsJobAdapter()
        with caplog.at_level(logging.WARNING):
            with patch("app.integrations.adapters.usajobs_adapter._get_api_key", return_value="test-key"), \
                 patch("app.integrations.adapters.usajobs_adapter._fetch_usajobs", side_effect=Exception("timeout")):
                await adapter.fetch_jobs(None, "jobs", "Fort Worth, TX")

        warnings = [r for r in caplog.records if r.levelno == logging.WARNING and "usajobs" in r.message.lower()]
        assert len(warnings) >= 1

    def test_no_log_at_import_time(self, caplog):
        import importlib
        import app.integrations.adapters.usajobs_adapter as mod

        caplog.clear()
        with caplog.at_level(logging.WARNING):
            importlib.reload(mod)
        import_warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert len(import_warnings) == 0

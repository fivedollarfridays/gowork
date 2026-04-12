"""Tests for live TWC job adapter."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.integrations.adapters.twc_adapter import TWCJobAdapter


@pytest.fixture
def adapter():
    return TWCJobAdapter()


class TestTWCAdapter:
    @pytest.mark.asyncio
    async def test_returns_list(self, adapter):
        """fetch_jobs always returns a list."""
        session = AsyncMock()
        with patch("app.integrations.adapters.twc_adapter._fetch_twc_jobs", return_value=[]):
            result = await adapter.fetch_jobs(session, "warehouse", "Fort Worth, TX")
            assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_normalizes_job_format(self, adapter):
        """Results must have standard job dict keys."""
        mock_data = [{
            "title": "Warehouse Worker",
            "company": "ACME Corp",
            "location": "Fort Worth, TX",
            "url": "https://twc.texas.gov/jobs/123",
            "source": "twc",
            "fair_chance": 0,
        }]
        session = AsyncMock()
        with patch("app.integrations.adapters.twc_adapter._fetch_twc_jobs", return_value=mock_data):
            result = await adapter.fetch_jobs(session, "warehouse", "Fort Worth, TX")
            assert len(result) == 1
            job = result[0]
            assert "title" in job
            assert "source" in job
            assert job["source"] == "twc"

    @pytest.mark.asyncio
    async def test_graceful_degradation(self, adapter):
        """Returns empty list on API failure."""
        session = AsyncMock()
        with patch("app.integrations.adapters.twc_adapter._fetch_twc_jobs", side_effect=Exception("API down")):
            result = await adapter.fetch_jobs(session, "warehouse", "Fort Worth, TX")
            assert result == []

    @pytest.mark.asyncio
    async def test_source_field_is_twc(self, adapter):
        """All results must have source='twc'."""
        mock_data = [{"title": "Driver", "company": "Co", "location": "FW", "url": "https://twc.texas.gov/1", "source": "twc", "fair_chance": 0}]
        session = AsyncMock()
        with patch("app.integrations.adapters.twc_adapter._fetch_twc_jobs", return_value=mock_data):
            result = await adapter.fetch_jobs(session, "driver", "Fort Worth, TX")
            for job in result:
                assert job["source"] == "twc"

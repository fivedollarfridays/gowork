"""Tests for live USAJobs adapter."""

import pytest
from unittest.mock import AsyncMock, patch

from app.integrations.adapters.usajobs_adapter import USAJobsJobAdapter


@pytest.fixture
def adapter():
    return USAJobsJobAdapter()


class TestUSAJobsAdapter:
    @pytest.mark.asyncio
    async def test_returns_list(self, adapter):
        session = AsyncMock()
        with patch("app.integrations.adapters.usajobs_adapter._fetch_usajobs", return_value=[]):
            result = await adapter.fetch_jobs(session, "analyst", "Fort Worth, TX")
            assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_normalizes_format(self, adapter):
        mock_data = [{
            "title": "IT Specialist",
            "company": "Department of Defense",
            "location": "Fort Worth, TX",
            "url": "https://www.usajobs.gov/job/123",
            "source": "usajobs",
            "fair_chance": 0,
        }]
        session = AsyncMock()
        with patch("app.integrations.adapters.usajobs_adapter._get_api_key", return_value="test-key"), \
             patch("app.integrations.adapters.usajobs_adapter._fetch_usajobs", return_value=mock_data):
            result = await adapter.fetch_jobs(session, "IT", "Fort Worth, TX")
            assert len(result) == 1
            assert result[0]["source"] == "usajobs"

    @pytest.mark.asyncio
    async def test_graceful_degradation_no_api_key(self, adapter):
        """Returns empty list when API key is missing."""
        session = AsyncMock()
        with patch("app.integrations.adapters.usajobs_adapter._get_api_key", return_value=""):
            result = await adapter.fetch_jobs(session, "analyst", "Fort Worth, TX")
            assert result == []

    @pytest.mark.asyncio
    async def test_graceful_degradation_api_error(self, adapter):
        session = AsyncMock()
        with patch("app.integrations.adapters.usajobs_adapter._get_api_key", return_value="test-key"), \
             patch("app.integrations.adapters.usajobs_adapter._fetch_usajobs", side_effect=Exception("API error")):
            result = await adapter.fetch_jobs(session, "analyst", "Fort Worth, TX")
            assert result == []

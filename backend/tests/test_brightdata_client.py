"""Tests for BrightData API client."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.integrations.brightdata.client import BrightDataClient
from app.integrations.brightdata.types import (
    BrightDataAPIError,
    BrightDataConfigError,
    CrawlProgress,
    CrawlResult,
    CrawlStatus,
)


class TestBrightDataClientInit:
    def test_raises_config_error_when_api_key_empty(self):
        with pytest.raises(BrightDataConfigError):
            BrightDataClient(api_key="", dataset_id="ds-123")

    def test_raises_config_error_when_dataset_id_empty(self):
        with pytest.raises(BrightDataConfigError):
            BrightDataClient(api_key="key-123", dataset_id="")

    def test_creates_client_with_valid_config(self):
        client = BrightDataClient(api_key="key-123", dataset_id="ds-123")
        assert client._api_key == "key-123"
        assert client._dataset_id == "ds-123"


class TestTriggerCrawl:
    @pytest.mark.asyncio
    async def test_trigger_crawl_success(self):
        client = BrightDataClient(api_key="key-123", dataset_id="ds-123")
        mock_response = httpx.Response(
            200,
            json={"snapshot_id": "snap-abc"},
            request=httpx.Request("POST", "https://example.com"),
        )
        with patch.object(client._http, "post", new_callable=AsyncMock, return_value=mock_response):
            snapshot_id = await client.trigger_crawl(["https://indeed.com/jobs"])
        assert snapshot_id == "snap-abc"

    @pytest.mark.asyncio
    async def test_trigger_crawl_http_error(self):
        client = BrightDataClient(api_key="key-123", dataset_id="ds-123")
        mock_response = httpx.Response(
            400,
            json={"error": "bad request"},
            request=httpx.Request("POST", "https://example.com"),
        )
        with patch.object(client._http, "post", new_callable=AsyncMock, return_value=mock_response):
            with pytest.raises(BrightDataAPIError) as exc_info:
                await client.trigger_crawl(["https://indeed.com/jobs"])
            assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_trigger_crawl_server_error(self):
        client = BrightDataClient(api_key="key-123", dataset_id="ds-123")
        mock_response = httpx.Response(
            500,
            text="Internal Server Error",
            request=httpx.Request("POST", "https://example.com"),
        )
        with patch.object(client._http, "post", new_callable=AsyncMock, return_value=mock_response):
            with pytest.raises(BrightDataAPIError) as exc_info:
                await client.trigger_crawl(["https://indeed.com/jobs"])
            assert exc_info.value.status_code == 500


class TestGetSnapshotStatus:
    @pytest.mark.asyncio
    async def test_status_running_returns_progress(self):
        client = BrightDataClient(api_key="key-123", dataset_id="ds-123")
        mock_response = httpx.Response(
            202,
            json={"status": "running", "progress": 0.5},
            request=httpx.Request("GET", "https://example.com"),
        )
        with patch.object(client._http, "get", new_callable=AsyncMock, return_value=mock_response):
            result = await client.get_snapshot_status("snap-abc")
        assert isinstance(result, CrawlProgress)
        assert result.status == CrawlStatus.RUNNING
        assert result.snapshot_id == "snap-abc"

    @pytest.mark.asyncio
    async def test_status_ready_returns_result(self):
        client = BrightDataClient(api_key="key-123", dataset_id="ds-123")
        jobs = [{"title": "Warehouse Worker", "company": "Acme"}]
        mock_response = httpx.Response(
            200,
            json=jobs,
            request=httpx.Request("GET", "https://example.com"),
        )
        with patch.object(client._http, "get", new_callable=AsyncMock, return_value=mock_response):
            result = await client.get_snapshot_status("snap-abc")
        assert isinstance(result, CrawlResult)
        assert result.snapshot_id == "snap-abc"
        assert len(result.jobs) == 1
        assert result.jobs[0]["title"] == "Warehouse Worker"

    @pytest.mark.asyncio
    async def test_status_http_error(self):
        client = BrightDataClient(api_key="key-123", dataset_id="ds-123")
        mock_response = httpx.Response(
            404,
            json={"error": "snapshot not found"},
            request=httpx.Request("GET", "https://example.com"),
        )
        with patch.object(client._http, "get", new_callable=AsyncMock, return_value=mock_response):
            with pytest.raises(BrightDataAPIError) as exc_info:
                await client.get_snapshot_status("snap-bad")
            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_status_non_json_error(self):
        """Non-JSON error response uses raw text as detail."""
        client = BrightDataClient(api_key="key-123", dataset_id="ds-123")
        mock_response = httpx.Response(
            503,
            text="Service Unavailable",
            request=httpx.Request("GET", "https://example.com"),
        )
        with patch.object(client._http, "get", new_callable=AsyncMock, return_value=mock_response):
            with pytest.raises(BrightDataAPIError) as exc_info:
                await client.get_snapshot_status("snap-err")
            assert exc_info.value.status_code == 503
            assert "Service Unavailable" in exc_info.value.detail


class TestClose:
    @pytest.mark.asyncio
    async def test_close_closes_http_client(self):
        client = BrightDataClient(api_key="key-123", dataset_id="ds-123")
        with patch.object(client._http, "aclose", new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        with patch.object(BrightDataClient, "close", new_callable=AsyncMock) as mock_close:
            async with BrightDataClient(api_key="key-123", dataset_id="ds-123") as client:
                assert isinstance(client, BrightDataClient)
            mock_close.assert_called_once()

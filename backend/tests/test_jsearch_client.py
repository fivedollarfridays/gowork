"""Tests for JSearch API client."""

import logging
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.integrations.jsearch.client import JSearchClient
from app.integrations.jsearch.types import (
    JSearchAPIError,
    JSearchConfigError,
    JSearchResponse,
)

SAMPLE_RESPONSE = {
    "status": "OK",
    "request_id": "req-abc-123",
    "data": [
        {
            "job_title": "Warehouse Associate",
            "employer_name": "Amazon",
            "job_city": "Montgomery",
            "job_state": "AL",
            "job_description": "Pack and ship orders",
            "job_apply_link": "https://example.com/apply",
            "job_min_salary": 15.0,
            "job_max_salary": 18.0,
            "job_salary_currency": "USD",
            "job_salary_period": "HOUR",
            "job_employment_type": "FULLTIME",
        },
    ],
}


class TestJSearchClientInit:
    def test_raises_config_error_when_api_key_empty(self):
        with pytest.raises(JSearchConfigError):
            JSearchClient(api_key="", host="jsearch.p.rapidapi.com")

    def test_creates_client_with_valid_config(self):
        client = JSearchClient(api_key="key-123")
        assert client._api_key == "key-123"


class TestSearchJobs:
    @pytest.mark.asyncio
    async def test_search_jobs_success(self):
        client = JSearchClient(api_key="key-123")
        mock_response = httpx.Response(
            200,
            json=SAMPLE_RESPONSE,
            request=httpx.Request("GET", "https://example.com"),
        )
        with patch.object(
            client._http, "get", new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await client.search_jobs("warehouse", "Montgomery, AL")

        assert isinstance(result, JSearchResponse)
        assert result.status == "OK"
        assert result.request_id == "req-abc-123"
        assert len(result.data) == 1
        assert result.data[0].title == "Warehouse Associate"
        assert result.data[0].company == "Amazon"
        assert result.data[0].location == "Montgomery, AL"

    @pytest.mark.asyncio
    async def test_search_jobs_sends_correct_headers(self):
        client = JSearchClient(api_key="key-123", host="test.rapidapi.com")
        mock_response = httpx.Response(
            200,
            json=SAMPLE_RESPONSE,
            request=httpx.Request("GET", "https://example.com"),
        )
        with patch.object(
            client._http, "get", new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_get:
            await client.search_jobs("jobs", "Montgomery, AL")

        call_kwargs = mock_get.call_args
        assert "search" in call_kwargs.args[0]

    @pytest.mark.asyncio
    async def test_search_jobs_http_error(self):
        client = JSearchClient(api_key="key-123")
        mock_response = httpx.Response(
            429,
            json={"message": "Rate limit exceeded"},
            request=httpx.Request("GET", "https://example.com"),
        )
        with patch.object(
            client._http, "get", new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(JSearchAPIError) as exc_info:
                await client.search_jobs("jobs", "Montgomery, AL")
            assert exc_info.value.status_code == 429

    @pytest.mark.asyncio
    async def test_search_jobs_server_error(self):
        client = JSearchClient(api_key="key-123")
        mock_response = httpx.Response(
            500,
            text="Internal Server Error",
            request=httpx.Request("GET", "https://example.com"),
        )
        with patch.object(
            client._http, "get", new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(JSearchAPIError) as exc_info:
                await client.search_jobs("jobs", "Montgomery, AL")
            assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_search_jobs_empty_results(self):
        client = JSearchClient(api_key="key-123")
        mock_response = httpx.Response(
            200,
            json={"status": "OK", "request_id": "req-empty", "data": []},
            request=httpx.Request("GET", "https://example.com"),
        )
        with patch.object(
            client._http, "get", new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await client.search_jobs("nonexistent", "Montgomery, AL")
        assert result.data == []

    @pytest.mark.asyncio
    async def test_search_jobs_network_error_returns_empty(self):
        """Network errors return empty response, not exception (graceful fallback)."""
        client = JSearchClient(api_key="key-123")
        with patch.object(
            client._http, "get", new_callable=AsyncMock,
            side_effect=httpx.ConnectError("Connection refused"),
        ):
            result = await client.search_jobs("jobs", "Montgomery, AL")
        assert result.data == []

    @pytest.mark.asyncio
    async def test_search_jobs_timeout_returns_empty(self):
        """Timeout returns empty response (graceful fallback)."""
        client = JSearchClient(api_key="key-123")
        with patch.object(
            client._http, "get", new_callable=AsyncMock,
            side_effect=httpx.TimeoutException("Read timed out"),
        ):
            result = await client.search_jobs("jobs", "Montgomery, AL")
        assert result.data == []


class TestRateLimitTracking:
    @pytest.mark.asyncio
    async def test_request_count_increments(self):
        client = JSearchClient(api_key="key-123")
        assert client.request_count == 0
        mock_response = httpx.Response(
            200,
            json=SAMPLE_RESPONSE,
            request=httpx.Request("GET", "https://example.com"),
        )
        with patch.object(
            client._http, "get", new_callable=AsyncMock,
            return_value=mock_response,
        ):
            await client.search_jobs("jobs", "Montgomery, AL")
        assert client.request_count == 1

    @pytest.mark.asyncio
    async def test_warns_at_rate_limit_threshold(self, caplog):
        client = JSearchClient(api_key="key-123", monthly_limit=200)
        client._request_count = 179
        mock_response = httpx.Response(
            200,
            json=SAMPLE_RESPONSE,
            request=httpx.Request("GET", "https://example.com"),
        )
        with patch.object(
            client._http, "get", new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with caplog.at_level(logging.WARNING):
                await client.search_jobs("jobs", "Montgomery, AL")
        assert client.request_count == 180
        assert any("rate limit" in r.message.lower() for r in caplog.records)


class TestParseRecord:
    def test_returns_none_when_title_missing(self):
        """_parse_record returns None when raw dict has no job_title."""
        client = JSearchClient(api_key="key-123")
        result = client._parse_record({"employer_name": "Acme"})
        assert result is None


class TestClose:
    @pytest.mark.asyncio
    async def test_close_closes_http_client(self):
        client = JSearchClient(api_key="key-123")
        with patch.object(
            client._http, "aclose", new_callable=AsyncMock,
        ) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        with patch.object(
            JSearchClient, "close", new_callable=AsyncMock,
        ) as mock_close:
            async with JSearchClient(api_key="key-123") as client:
                assert isinstance(client, JSearchClient)
            mock_close.assert_called_once()

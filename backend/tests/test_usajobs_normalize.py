"""Tests for USAJobs adapter internals -- _normalize and _fetch_usajobs.

Covers uncovered lines 44-64 (API call path) and 69-73 (_normalize).
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.integrations.adapters.usajobs_adapter import _normalize, _fetch_usajobs


class TestNormalize:
    """_normalize transforms raw USAJobs API items to standard format."""

    def test_basic_normalization(self):
        """Standard item with MatchedObjectDescriptor."""
        item = {
            "MatchedObjectDescriptor": {
                "PositionTitle": "IT Specialist",
                "OrganizationName": "Department of Veterans Affairs",
                "PositionLocation": [{"LocationName": "Fort Worth, TX"}],
                "PositionURI": "https://usajobs.gov/job/123",
            },
        }
        result = _normalize(item)
        assert result["title"] == "IT Specialist"
        assert result["company"] == "Department of Veterans Affairs"
        assert result["location"] == "Fort Worth, TX"
        assert result["url"] == "https://usajobs.gov/job/123"
        assert result["source"] == "usajobs"
        assert result["fair_chance"] == 0

    def test_missing_position_title_defaults(self):
        """Missing PositionTitle defaults to 'Unknown'."""
        item = {
            "MatchedObjectDescriptor": {
                "OrganizationName": "DOD",
                "PositionLocation": [],
            },
        }
        result = _normalize(item)
        assert result["title"] == "Unknown"

    def test_missing_organization_defaults(self):
        """Missing OrganizationName defaults to 'U.S. Government'."""
        item = {
            "MatchedObjectDescriptor": {
                "PositionTitle": "Analyst",
                "PositionLocation": [{"LocationName": "DC"}],
            },
        }
        result = _normalize(item)
        assert result["company"] == "U.S. Government"

    def test_empty_position_location(self):
        """Empty PositionLocation list defaults location to empty string."""
        item = {
            "MatchedObjectDescriptor": {
                "PositionTitle": "Clerk",
                "PositionLocation": [],
            },
        }
        result = _normalize(item)
        assert result["location"] == ""

    def test_no_position_location_key(self):
        """Missing PositionLocation key uses default."""
        item = {
            "MatchedObjectDescriptor": {
                "PositionTitle": "Clerk",
            },
        }
        result = _normalize(item)
        assert result["location"] == ""

    def test_apply_uri_fallback(self):
        """When PositionURI is missing, falls back to ApplyURI list."""
        item = {
            "MatchedObjectDescriptor": {
                "PositionTitle": "Tester",
                "ApplyURI": ["https://usajobs.gov/apply/456"],
            },
        }
        result = _normalize(item)
        assert result["url"] == "https://usajobs.gov/apply/456"

    def test_no_uri_at_all(self):
        """No PositionURI and no ApplyURI results in empty URL."""
        item = {
            "MatchedObjectDescriptor": {
                "PositionTitle": "Specialist",
            },
        }
        result = _normalize(item)
        assert result["url"] == ""

    def test_item_without_matched_descriptor_uses_item(self):
        """If MatchedObjectDescriptor is missing, falls back to item itself."""
        item = {
            "PositionTitle": "Fallback Job",
            "OrganizationName": "Fallback Org",
            "PositionLocation": [{"LocationName": "Remote"}],
            "PositionURI": "https://example.com",
        }
        result = _normalize(item)
        assert result["title"] == "Fallback Job"
        assert result["company"] == "Fallback Org"
        assert result["location"] == "Remote"


class TestFetchUSAJobs:
    """_fetch_usajobs API call path."""

    @pytest.mark.anyio
    async def test_returns_empty_without_api_key(self):
        """No API key returns empty list immediately."""
        with patch("app.integrations.adapters.usajobs_adapter._get_api_key", return_value=""):
            result = await _fetch_usajobs("analyst", "Fort Worth, TX")
            assert result == []

    @pytest.mark.anyio
    async def test_successful_api_call(self):
        """Successful API call returns normalized jobs."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "SearchResult": {
                "SearchResultItems": [
                    {
                        "MatchedObjectDescriptor": {
                            "PositionTitle": "Budget Analyst",
                            "OrganizationName": "DOD",
                            "PositionLocation": [{"LocationName": "Fort Worth, TX"}],
                            "PositionURI": "https://usajobs.gov/job/789",
                        },
                    },
                ],
            },
        }
        mock_response.raise_for_status = MagicMock()
        mock_response.status_code = 200  # T13.92 retry helper inspects status_code

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.integrations.adapters.usajobs_adapter._get_api_key", return_value="test-key"), \
             patch("app.integrations.adapters.usajobs_adapter._get_email", return_value="test@example.com"), \
             patch("app.integrations.adapters.usajobs_adapter.httpx.AsyncClient", return_value=mock_client):
            result = await _fetch_usajobs("analyst", "Fort Worth, TX")

        assert len(result) == 1
        assert result[0]["title"] == "Budget Analyst"
        assert result[0]["source"] == "usajobs"

    @pytest.mark.anyio
    async def test_empty_search_results(self):
        """API returns empty search results."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "SearchResult": {"SearchResultItems": []},
        }
        mock_response.raise_for_status = MagicMock()
        mock_response.status_code = 200  # T13.92 retry helper inspects status_code

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.integrations.adapters.usajobs_adapter._get_api_key", return_value="test-key"), \
             patch("app.integrations.adapters.usajobs_adapter.httpx.AsyncClient", return_value=mock_client):
            result = await _fetch_usajobs("rare job", "Nowhere")

        assert result == []

    @pytest.mark.anyio
    async def test_missing_email_uses_default(self):
        """Missing USAJOBS_EMAIL falls back to default user agent."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"SearchResult": {"SearchResultItems": []}}
        mock_response.raise_for_status = MagicMock()
        mock_response.status_code = 200  # T13.92 retry helper inspects status_code

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.integrations.adapters.usajobs_adapter._get_api_key", return_value="test-key"), \
             patch("app.integrations.adapters.usajobs_adapter._get_email", return_value=""), \
             patch("app.integrations.adapters.usajobs_adapter.httpx.AsyncClient", return_value=mock_client):
            result = await _fetch_usajobs("analyst", "DC")

        # Should still succeed; email falls back to default
        assert result == []
        # Verify the headers used the default email
        call_kwargs = mock_client.get.call_args
        headers = call_kwargs.kwargs.get("headers") or call_kwargs[1].get("headers", {})
        assert headers.get("User-Agent") == "montgowork@example.com"

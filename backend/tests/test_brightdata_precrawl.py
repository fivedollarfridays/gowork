"""Tests for Montgomery pre-crawl pipeline."""

from unittest.mock import AsyncMock, patch

import pytest

from app.core.database import get_async_session_factory
from app.core.queries import insert_job_listings
from app.integrations.brightdata.precrawl import (
    _has_recent_data,
    build_search_urls,
    precrawl_montgomery_jobs,
)
from app.integrations.brightdata.types import (
    BrightDataConfigError,
    CrawlResult,
)


@pytest.fixture
async def db_session(test_engine):
    factory = get_async_session_factory()
    async with factory() as session:
        yield session

_CLIENT_PATCH = "app.integrations.brightdata.precrawl.BrightDataClient"
_SETTINGS_PATCH = "app.integrations.brightdata.precrawl.get_settings"
_POLL_PATCH = "app.integrations.brightdata.precrawl.poll_until_ready"
_STORE_PATCH = "app.integrations.brightdata.precrawl.store_crawl_results"
_STALE_PATCH = "app.integrations.brightdata.precrawl._has_recent_data"


def _mock_settings(api_key="key-123", dataset_id="ds-123"):
    s = AsyncMock()
    s.brightdata_api_key = api_key
    s.brightdata_dataset_id = dataset_id
    return s


class TestHasRecentData:
    @pytest.mark.anyio
    async def test_returns_false_when_no_data(self, db_session):
        assert await _has_recent_data(db_session) is False

    @pytest.mark.anyio
    async def test_returns_true_when_recent_brightdata_rows(self, db_session):
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat()
        await insert_job_listings(db_session, [{
            "title": "Job", "source": "brightdata:snap-1",
            "scraped_at": now, "expires_at": now,
        }])
        assert await _has_recent_data(db_session) is True


class TestBuildSearchUrls:
    def test_returns_multiple_urls(self):
        urls = build_search_urls()
        assert len(urls) >= 3

    def test_urls_target_montgomery(self):
        urls = build_search_urls()
        for url in urls:
            assert "montgomery" in url.lower() or "Montgomery" in url


class TestPrecrawlMontgomeryJobs:
    @pytest.mark.asyncio
    async def test_full_flow(self):
        """Trigger -> poll -> cache -> return result."""
        mock_client = AsyncMock()
        mock_client.trigger_crawl = AsyncMock(return_value="snap-pre")
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        jobs = [{"title": "CNA"}, {"title": "Driver"}]
        crawl_result = CrawlResult(snapshot_id="snap-pre", jobs=jobs)

        with (
            patch(_SETTINGS_PATCH, return_value=_mock_settings()),
            patch(_CLIENT_PATCH, return_value=mock_client),
            patch(_POLL_PATCH, new_callable=AsyncMock, return_value=crawl_result),
            patch(_STORE_PATCH, new_callable=AsyncMock, return_value=2),
            patch(_STALE_PATCH, new_callable=AsyncMock, return_value=False),
        ):
            result = await precrawl_montgomery_jobs(AsyncMock())

        assert result["snapshot_id"] == "snap-pre"
        assert result["jobs_cached"] == 2
        assert result["skipped"] is False

    @pytest.mark.asyncio
    async def test_skips_when_recent_data_exists(self):
        """Should skip crawl if recent data < 24h old."""
        with (
            patch(_SETTINGS_PATCH, return_value=_mock_settings()),
            patch(_STALE_PATCH, new_callable=AsyncMock, return_value=True),
        ):
            result = await precrawl_montgomery_jobs(AsyncMock())

        assert result["skipped"] is True
        assert result["jobs_cached"] == 0

    @pytest.mark.asyncio
    async def test_handles_no_api_key(self):
        """Should raise BrightDataConfigError when key is empty."""
        with (
            patch(_SETTINGS_PATCH, return_value=_mock_settings(api_key="")),
            patch(_STALE_PATCH, new_callable=AsyncMock, return_value=False),
        ):
            with pytest.raises(BrightDataConfigError):
                await precrawl_montgomery_jobs(AsyncMock())

    @pytest.mark.asyncio
    async def test_empty_crawl_results(self):
        """Zero jobs from crawl is not an error."""
        mock_client = AsyncMock()
        mock_client.trigger_crawl = AsyncMock(return_value="snap-empty")
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        crawl_result = CrawlResult(snapshot_id="snap-empty", jobs=[])

        with (
            patch(_SETTINGS_PATCH, return_value=_mock_settings()),
            patch(_CLIENT_PATCH, return_value=mock_client),
            patch(_POLL_PATCH, new_callable=AsyncMock, return_value=crawl_result),
            patch(_STORE_PATCH, new_callable=AsyncMock, return_value=0),
            patch(_STALE_PATCH, new_callable=AsyncMock, return_value=False),
        ):
            result = await precrawl_montgomery_jobs(AsyncMock())

        assert result["jobs_cached"] == 0
        assert result["skipped"] is False

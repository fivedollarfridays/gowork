"""Tests for Montgomery pre-crawl pipeline."""

from unittest.mock import AsyncMock, patch

import pytest

from app.core.database import get_async_session_factory
from app.core.queries_jobs import insert_job_listings
from app.integrations.brightdata.precrawl import (
    _has_recent_data,
    build_keyword_searches,
    build_search_urls,
    get_crawl_domains,
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


def _mock_settings(api_key="key-123", dataset_id="ds-123", job_domains="indeed.com"):
    s = AsyncMock()
    s.brightdata_api_key = api_key
    s.brightdata_dataset_id = dataset_id
    s.brightdata_job_domains = job_domains
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
    def test_build_search_urls_returns_list(self):
        """build_search_urls returns a list of Indeed URL strings."""
        urls = build_search_urls()
        assert isinstance(urls, list)
        assert len(urls) == 15
        for url in urls:
            assert url.startswith("https://www.indeed.com/jobs")

    def test_build_search_urls_includes_location(self):
        """Each URL contains Montgomery (URL-encoded) in the location parameter."""
        urls = build_search_urls()
        for url in urls:
            assert "Montgomery" in url

    def test_build_search_urls_includes_fromage(self):
        """Each URL includes fromage=7 for recent jobs."""
        urls = build_search_urls()
        for url in urls:
            assert "fromage=7" in url


class TestBuildKeywordSearches:
    def test_returns_15_searches(self):
        """15 keywords x 1 platform (Indeed) = 15 with default config."""
        with patch(_SETTINGS_PATCH, return_value=_mock_settings()):
            searches = build_keyword_searches()
        assert len(searches) == 15

    def test_indeed_searches_target_montgomery(self):
        with patch(_SETTINGS_PATCH, return_value=_mock_settings()):
            searches = build_keyword_searches()
        indeed = [s for s in searches if s["domain"] == "indeed.com"]
        assert len(indeed) == 15
        for s in indeed:
            assert "Montgomery" in s["location"]
            assert s["country"] == "US"

    def test_all_searches_are_indeed(self):
        with patch(_SETTINGS_PATCH, return_value=_mock_settings()):
            searches = build_keyword_searches()
        for s in searches:
            assert s["domain"] == "indeed.com"

    def test_includes_required_keywords(self):
        """All 15 required keywords must be present."""
        with patch(_SETTINGS_PATCH, return_value=_mock_settings()):
            searches = build_keyword_searches()
        indeed_keywords = {s["keyword_search"] for s in searches if s["domain"] == "indeed.com"}
        required = {
            "jobs", "warehouse", "healthcare", "customer service", "retail",
            "manufacturing", "food service", "construction", "driver",
            "cashier", "cleaning", "security", "maintenance",
            "administrative", "entry level",
        }
        assert required == indeed_keywords

    def test_searches_only_include_required_fields(self):
        with patch(_SETTINGS_PATCH, return_value=_mock_settings()):
            searches = build_keyword_searches()
        allowed = {"country", "domain", "keyword_search", "location"}
        for s in searches:
            assert set(s.keys()) == allowed


class TestGetCrawlDomains:
    def test_default_is_indeed_only(self):
        """Default config returns only indeed.com."""
        with patch(_SETTINGS_PATCH, return_value=_mock_settings()):
            domains = get_crawl_domains()
        assert domains == ["indeed.com"]

    def test_multi_domain_config(self):
        """Comma-separated config returns multiple domains."""
        with patch(_SETTINGS_PATCH, return_value=_mock_settings(job_domains="indeed.com,linkedin.com")):
            domains = get_crawl_domains()
        assert domains == ["indeed.com", "linkedin.com"]

    def test_handles_whitespace(self):
        """Whitespace around domains is stripped."""
        with patch(_SETTINGS_PATCH, return_value=_mock_settings(job_domains="indeed.com, linkedin.com ")):
            domains = get_crawl_domains()
        assert domains == ["indeed.com", "linkedin.com"]

    def test_empty_string_uses_default(self):
        """Empty string falls back to indeed.com."""
        with patch(_SETTINGS_PATCH, return_value=_mock_settings(job_domains="")):
            domains = get_crawl_domains()
        assert domains == ["indeed.com"]

    def test_blank_entries_filtered_out(self):
        """Blank entries from trailing commas are filtered."""
        with patch(_SETTINGS_PATCH, return_value=_mock_settings(job_domains="indeed.com,,linkedin.com,")):
            domains = get_crawl_domains()
        assert domains == ["indeed.com", "linkedin.com"]


class TestMultiDomainKeywordSearches:
    def test_multi_domain_doubles_search_count(self):
        """Two domains with 15 keywords = 30 searches."""
        with patch(_SETTINGS_PATCH, return_value=_mock_settings(job_domains="indeed.com,linkedin.com")):
            searches = build_keyword_searches()
        assert len(searches) == 30

    def test_multi_domain_has_all_domains(self):
        """Each configured domain appears in the searches."""
        with patch(_SETTINGS_PATCH, return_value=_mock_settings(job_domains="indeed.com,linkedin.com")):
            searches = build_keyword_searches()
        domains_found = {s["domain"] for s in searches}
        assert domains_found == {"indeed.com", "linkedin.com"}

    def test_multi_domain_has_all_keywords_per_domain(self):
        """Every keyword appears for each domain."""
        with patch(_SETTINGS_PATCH, return_value=_mock_settings(job_domains="indeed.com,linkedin.com")):
            searches = build_keyword_searches()
        for domain in ("indeed.com", "linkedin.com"):
            keywords = {s["keyword_search"] for s in searches if s["domain"] == domain}
            assert len(keywords) == 15


class TestPrecrawlMontgomeryJobs:
    @pytest.mark.asyncio
    async def test_full_flow(self):
        """Trigger -> poll -> cache -> return result (single domain default)."""
        mock_client = AsyncMock()
        mock_client.trigger_keyword_crawl = AsyncMock(return_value="snap-pre")
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

        assert result["snapshot_id"] is not None
        assert result["jobs_cached"] == 2
        assert result["skipped"] is False
        assert result["errors"] == []

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
    async def test_partial_domain_failure_continues(self):
        """If one domain's crawl fails, others still succeed."""
        mock_client = AsyncMock()
        mock_client.trigger_keyword_crawl = AsyncMock(
            side_effect=["snap-ok", Exception("linkedin crawl failed")]
        )
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        jobs = [{"title": "CNA"}]
        crawl_result = CrawlResult(snapshot_id="snap-ok", jobs=jobs)

        with (
            patch(_SETTINGS_PATCH, return_value=_mock_settings(
                job_domains="indeed.com,linkedin.com"
            )),
            patch(_CLIENT_PATCH, return_value=mock_client),
            patch(_POLL_PATCH, new_callable=AsyncMock, return_value=crawl_result),
            patch(_STORE_PATCH, new_callable=AsyncMock, return_value=1),
            patch(_STALE_PATCH, new_callable=AsyncMock, return_value=False),
        ):
            result = await precrawl_montgomery_jobs(AsyncMock())

        assert result["skipped"] is False
        assert result["jobs_cached"] == 1
        assert len(result["errors"]) == 1
        assert "linkedin" in result["errors"][0].lower()

    @pytest.mark.asyncio
    async def test_all_domains_fail_returns_zero(self):
        """If all domain crawls fail, return zero cached with errors."""
        mock_client = AsyncMock()
        mock_client.trigger_keyword_crawl = AsyncMock(
            side_effect=Exception("crawl failed")
        )
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with (
            patch(_SETTINGS_PATCH, return_value=_mock_settings(
                job_domains="indeed.com,linkedin.com"
            )),
            patch(_CLIENT_PATCH, return_value=mock_client),
            patch(_STALE_PATCH, new_callable=AsyncMock, return_value=False),
        ):
            result = await precrawl_montgomery_jobs(AsyncMock())

        assert result["skipped"] is False
        assert result["jobs_cached"] == 0
        assert len(result["errors"]) == 2

    @pytest.mark.asyncio
    async def test_multi_domain_aggregates_cached_count(self):
        """Multiple successful domains aggregate their cached job counts."""
        mock_client = AsyncMock()
        mock_client.trigger_keyword_crawl = AsyncMock(
            side_effect=["snap-indeed", "snap-linkedin"]
        )
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        result_indeed = CrawlResult(snapshot_id="snap-indeed", jobs=[{"title": "CNA"}])
        result_linkedin = CrawlResult(snapshot_id="snap-linkedin", jobs=[{"title": "Driver"}])

        with (
            patch(_SETTINGS_PATCH, return_value=_mock_settings(
                job_domains="indeed.com,linkedin.com"
            )),
            patch(_CLIENT_PATCH, return_value=mock_client),
            patch(_POLL_PATCH, new_callable=AsyncMock, side_effect=[result_indeed, result_linkedin]),
            patch(_STORE_PATCH, new_callable=AsyncMock, side_effect=[3, 5]),
            patch(_STALE_PATCH, new_callable=AsyncMock, return_value=False),
        ):
            result = await precrawl_montgomery_jobs(AsyncMock())

        assert result["jobs_cached"] == 8
        assert result["skipped"] is False
        assert result["errors"] == []

    @pytest.mark.asyncio
    async def test_empty_crawl_results(self):
        """Zero jobs from crawl is not an error."""
        mock_client = AsyncMock()
        mock_client.trigger_keyword_crawl = AsyncMock(return_value="snap-empty")
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

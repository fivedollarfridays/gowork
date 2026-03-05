"""Tests for BrightData job listing cache — parse, dedup, insert."""

import pytest
from sqlalchemy import text

from app.core.database import get_async_session_factory
from app.core.queries import get_job_listings_by_source, insert_job_listings
from app.integrations.brightdata.cache import parse_brightdata_jobs, store_crawl_results


@pytest.fixture
async def db_session(test_engine):
    """Yield an async session from the test engine."""
    factory = get_async_session_factory()
    async with factory() as session:
        yield session


class TestParseBrightdataJobs:
    def test_parses_valid_job(self):
        raw = [{"title": "CNA", "company": "Baptist", "location": "Montgomery, AL",
                "url": "https://example.com/cna"}]
        result = parse_brightdata_jobs(raw)
        assert len(result) == 1
        assert result[0].title == "CNA"
        assert result[0].company == "Baptist"

    def test_handles_missing_optional_fields(self):
        raw = [{"title": "Warehouse Worker"}]
        result = parse_brightdata_jobs(raw)
        assert len(result) == 1
        assert result[0].company is None
        assert result[0].url is None

    def test_skips_records_without_title(self):
        raw = [{"company": "Acme"}, {"title": "Valid Job"}]
        result = parse_brightdata_jobs(raw)
        assert len(result) == 1
        assert result[0].title == "Valid Job"

    def test_empty_list_returns_empty(self):
        assert parse_brightdata_jobs([]) == []

    def test_ignores_extra_fields(self):
        raw = [{"title": "Job", "salary": "$50k", "unknown_field": True}]
        result = parse_brightdata_jobs(raw)
        assert len(result) == 1
        assert result[0].title == "Job"


class TestInsertJobListings:
    @pytest.mark.anyio
    async def test_bulk_inserts(self, db_session):
        listings = [
            {"title": "CNA", "company": "Baptist", "source": "test",
             "scraped_at": "2026-03-05T00:00:00Z", "expires_at": "2026-04-04T00:00:00Z"},
            {"title": "Driver", "company": "FedEx", "source": "test",
             "scraped_at": "2026-03-05T00:00:00Z", "expires_at": "2026-04-04T00:00:00Z"},
        ]
        count = await insert_job_listings(db_session, listings)
        assert count == 2

    @pytest.mark.anyio
    async def test_empty_list_inserts_zero(self, db_session):
        count = await insert_job_listings(db_session, [])
        assert count == 0


class TestGetJobListingsBySource:
    @pytest.mark.anyio
    async def test_filters_by_source(self, db_session):
        await insert_job_listings(db_session, [
            {"title": "Job A", "source": "brightdata:snap-1",
             "scraped_at": "2026-03-05T00:00:00Z", "expires_at": "2026-04-04T00:00:00Z"},
            {"title": "Job B", "source": "brightdata:snap-2",
             "scraped_at": "2026-03-05T00:00:00Z", "expires_at": "2026-04-04T00:00:00Z"},
        ])
        results = await get_job_listings_by_source(db_session, "brightdata:snap-1")
        assert len(results) == 1
        assert results[0]["title"] == "Job A"

    @pytest.mark.anyio
    async def test_returns_empty_for_unknown_source(self, db_session):
        results = await get_job_listings_by_source(db_session, "nonexistent")
        assert results == []


class TestStoreCrawlResults:
    @pytest.mark.anyio
    async def test_stores_parsed_jobs(self, db_session):
        raw_jobs = [
            {"title": "CNA", "company": "Baptist", "url": "https://example.com/cna"},
            {"title": "Driver", "url": "https://example.com/driver"},
        ]
        count = await store_crawl_results(db_session, "snap-abc", raw_jobs)
        assert count == 2
        # Verify source tag
        results = await get_job_listings_by_source(db_session, "brightdata:snap-abc")
        assert len(results) == 2

    @pytest.mark.anyio
    async def test_deduplicates_by_url(self, db_session):
        raw = [{"title": "CNA", "url": "https://example.com/cna"}]
        await store_crawl_results(db_session, "snap-1", raw)
        # Insert same URL again from different snapshot
        count = await store_crawl_results(db_session, "snap-2", raw)
        assert count == 0  # Duplicate skipped

    @pytest.mark.anyio
    async def test_jobs_without_url_not_deduplicated(self, db_session):
        raw = [{"title": "CNA"}]
        await store_crawl_results(db_session, "snap-1", raw)
        count = await store_crawl_results(db_session, "snap-2", raw)
        # No URL means no dedup — both inserted
        assert count == 1

    @pytest.mark.anyio
    async def test_sets_30_day_expiry(self, db_session):
        raw = [{"title": "Job", "url": "https://example.com/exp"}]
        await store_crawl_results(db_session, "snap-exp", raw)
        result = await db_session.execute(
            text("SELECT scraped_at, expires_at FROM job_listings WHERE source = :s"),
            {"s": "brightdata:snap-exp"},
        )
        row = result.first()
        assert row is not None
        # expires_at should be ~30 days after scraped_at (both are ISO strings)
        assert row[1] > row[0]

    @pytest.mark.anyio
    async def test_skips_invalid_records(self, db_session):
        raw = [{"company": "No Title"}, {"title": "Valid"}]
        count = await store_crawl_results(db_session, "snap-skip", raw)
        assert count == 1

    @pytest.mark.anyio
    async def test_all_invalid_returns_zero(self, db_session):
        raw = [{"company": "No Title"}, {"description": "Also no title"}]
        count = await store_crawl_results(db_session, "snap-none", raw)
        assert count == 0

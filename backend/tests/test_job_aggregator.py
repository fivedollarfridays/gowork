"""Tests for unified job aggregator — parallel fetch, dedup, filters."""

from unittest.mock import patch

import pytest
from sqlalchemy import text

from app.core.database import get_async_session_factory
from app.core.queries_jobs import insert_job_listings
from app.integrations.job_aggregator import JobAggregator, _matches_source


@pytest.fixture
async def db_session(test_engine):
    """Yield an async session from the test engine."""
    factory = get_async_session_factory()
    async with factory() as session:
        yield session


def _make_listing(title, company, source, **kwargs):
    """Helper to create a job listing dict."""
    return {
        "title": title,
        "company": company,
        "source": source,
        "scraped_at": "2026-03-08T00:00:00Z",
        "expires_at": "2099-12-31T00:00:00Z",
        **kwargs,
    }


async def _seed_brightdata(session, count=3):
    """Insert sample BrightData-sourced jobs."""
    listings = [
        _make_listing("CNA", "Baptist Health", "brightdata:snap-1",
                       location="Montgomery, AL"),
        _make_listing("Warehouse Worker", "Amazon", "brightdata:snap-1",
                       location="Montgomery, AL"),
        _make_listing("Cashier", "Dollar General", "brightdata:snap-1",
                       location="Montgomery, AL"),
    ][:count]
    await insert_job_listings(session, listings)
    return listings


async def _seed_honestjobs(session, count=2):
    """Insert sample Honest Jobs listings with fair_chance."""
    listings = [
        _make_listing("Forklift Operator", "Goodwill", "honestjobs",
                       location="Montgomery, AL"),
        _make_listing("Custodial Tech", "ABM Industries", "honestjobs",
                       location="Montgomery, AL"),
    ][:count]
    for listing in listings:
        listing["fair_chance"] = 1
    for listing in listings:
        await session.execute(
            text(
                "INSERT INTO job_listings "
                "(title, company, location, source, scraped_at, expires_at, fair_chance) "
                "VALUES (:title, :company, :location, :source, :scraped_at, :expires_at, :fair_chance)"
            ),
            listing,
        )
    await session.commit()
    return listings


class TestAggregatorSearch:
    @pytest.mark.anyio
    async def test_returns_brightdata_cached(self, db_session):
        """Aggregator returns BrightData cached jobs."""
        await _seed_brightdata(db_session)
        agg = JobAggregator(db_session)
        results = await agg.search()
        brightdata = [j for j in results if j["source"].startswith("brightdata:")]
        assert len(brightdata) == 3

    @pytest.mark.anyio
    async def test_returns_honestjobs_cached(self, db_session):
        """Aggregator returns Honest Jobs seeded listings."""
        await _seed_honestjobs(db_session)
        agg = JobAggregator(db_session)
        results = await agg.search()
        honest = [j for j in results if j["source"] == "honestjobs"]
        assert len(honest) == 2

    @pytest.mark.anyio
    async def test_combines_all_sources(self, db_session):
        """Aggregator combines BrightData + Honest Jobs."""
        await _seed_brightdata(db_session, 2)
        await _seed_honestjobs(db_session, 1)
        agg = JobAggregator(db_session)
        results = await agg.search()
        assert len(results) == 3  # 2 + 1

    @pytest.mark.anyio
    async def test_deduplicates_across_sources(self, db_session):
        """Same job from BrightData and HonestJobs appears once."""
        await insert_job_listings(db_session, [
            _make_listing("Forklift Operator", "Goodwill", "brightdata:snap-1",
                           location="Montgomery, AL"),
        ])
        await _seed_honestjobs(db_session, 2)
        agg = JobAggregator(db_session)
        results = await agg.search()
        goodwill = [j for j in results if j.get("company") == "Goodwill"]
        assert len(goodwill) == 1


class TestAggregatorExceptionHandling:
    @pytest.mark.anyio
    async def test_continues_when_source_raises_exception(self, db_session):
        """When one source raises, others still return."""
        await _seed_honestjobs(db_session, 1)
        agg = JobAggregator(db_session)
        with patch.object(
            agg, "_brightdata_cached",
            side_effect=RuntimeError("BrightData DB error"),
        ):
            results = await agg.search()
        assert len(results) >= 1
        assert all(j["source"] == "honestjobs" for j in results)


class TestMatchesSource:
    def test_brightdata_filter_matches_prefix(self):
        assert _matches_source({"source": "brightdata:snap-1"}, "brightdata") is True

    def test_brightdata_filter_rejects_other(self):
        assert _matches_source({"source": "honestjobs"}, "brightdata") is False

    def test_exact_source_match(self):
        assert _matches_source({"source": "honestjobs"}, "honestjobs") is True

    def test_exact_source_no_match(self):
        assert _matches_source({"source": "honestjobs"}, "brightdata") is False

    def test_unknown_source_returns_false(self):
        assert _matches_source({"source": "brightdata:snap-1"}, "jsearch") is False


class TestAggregatorFilters:
    @pytest.mark.anyio
    async def test_filter_by_source(self, db_session):
        await _seed_brightdata(db_session, 2)
        await _seed_honestjobs(db_session, 1)
        agg = JobAggregator(db_session)
        results = await agg.search(source="honestjobs")
        assert len(results) == 1
        assert all(j["source"] == "honestjobs" for j in results)

    @pytest.mark.anyio
    async def test_filter_fair_chance_only(self, db_session):
        await _seed_brightdata(db_session, 2)
        await _seed_honestjobs(db_session, 1)
        agg = JobAggregator(db_session)
        results = await agg.search(fair_chance=True)
        assert len(results) == 1
        assert all(j.get("fair_chance") == 1 for j in results)

    @pytest.mark.anyio
    async def test_no_filter_returns_all(self, db_session):
        await _seed_brightdata(db_session, 2)
        await _seed_honestjobs(db_session, 1)
        agg = JobAggregator(db_session)
        results = await agg.search()
        assert len(results) == 3

    @pytest.mark.anyio
    async def test_jsearch_source_filter_returns_empty(self, db_session):
        """Filtering by removed jsearch source returns nothing, no error."""
        await _seed_brightdata(db_session, 2)
        agg = JobAggregator(db_session)
        results = await agg.search(source="jsearch")
        assert len(results) == 0


class TestJobsRoute:
    @pytest.mark.anyio
    async def test_list_jobs_returns_aggregated(self, client):
        resp = await client.get("/api/jobs/")
        assert resp.status_code == 200
        body = resp.json()
        assert "jobs" in body
        assert "total" in body

    @pytest.mark.anyio
    async def test_source_filter_param(self, client):
        resp = await client.get("/api/jobs/?source=honestjobs")
        assert resp.status_code == 200
        body = resp.json()
        for job in body["jobs"]:
            assert job["source"] == "honestjobs"

    @pytest.mark.anyio
    async def test_fair_chance_filter_param(self, client):
        resp = await client.get("/api/jobs/?fair_chance=true")
        assert resp.status_code == 200
        body = resp.json()
        for job in body["jobs"]:
            assert job.get("fair_chance") == 1

"""Tests for HonestJobsJobAdapter — wraps _honestjobs_cached query logic."""

import pytest
from sqlalchemy import text

from app.core.database import get_async_session_factory
from app.core.queries_jobs import insert_job_listings


@pytest.fixture
async def db_session(test_engine):
    factory = get_async_session_factory()
    async with factory() as session:
        yield session


def _make_listing(title, company, source, **kwargs):
    return {
        "title": title,
        "company": company,
        "source": source,
        "scraped_at": "2026-03-08T00:00:00Z",
        "expires_at": "2099-12-31T00:00:00Z",
        **kwargs,
    }


async def _seed_honestjobs(session):
    listings = [
        _make_listing("Forklift Operator", "Goodwill", "honestjobs",
                       location="Montgomery, AL"),
        _make_listing("Custodial Tech", "ABM Industries", "honestjobs",
                       location="Montgomery, AL"),
    ]
    for listing in listings:
        listing["fair_chance"] = 1
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


async def _seed_brightdata(session):
    await insert_job_listings(session, [
        _make_listing("CNA", "Baptist Health", "brightdata:snap-1",
                       location="Montgomery, AL"),
    ])


class TestHonestJobsAdapterFetchJobs:
    @pytest.mark.anyio
    async def test_returns_honestjobs_rows(self, db_session):
        await _seed_honestjobs(db_session)
        from app.integrations.adapters.honestjobs_adapter import HonestJobsJobAdapter

        adapter = HonestJobsJobAdapter()
        rows = await adapter.fetch_jobs(db_session, "jobs", "Montgomery, AL")
        assert len(rows) == 2

    @pytest.mark.anyio
    async def test_excludes_non_honestjobs_sources(self, db_session):
        await _seed_honestjobs(db_session)
        await _seed_brightdata(db_session)
        from app.integrations.adapters.honestjobs_adapter import HonestJobsJobAdapter

        adapter = HonestJobsJobAdapter()
        rows = await adapter.fetch_jobs(db_session, "jobs", "Montgomery, AL")
        assert all(r["source"] == "honestjobs" for r in rows)

    @pytest.mark.anyio
    async def test_returns_dicts(self, db_session):
        await _seed_honestjobs(db_session)
        from app.integrations.adapters.honestjobs_adapter import HonestJobsJobAdapter

        adapter = HonestJobsJobAdapter()
        rows = await adapter.fetch_jobs(db_session, "jobs", "Montgomery, AL")
        assert all(isinstance(r, dict) for r in rows)

    @pytest.mark.anyio
    async def test_empty_table_returns_empty_list(self, db_session):
        from app.integrations.adapters.honestjobs_adapter import HonestJobsJobAdapter

        adapter = HonestJobsJobAdapter()
        rows = await adapter.fetch_jobs(db_session, "jobs", "Montgomery, AL")
        assert rows == []


class TestHonestJobsAdapterMatchesAggregator:
    @pytest.mark.anyio
    async def test_byte_identical_to_aggregator(self, db_session):
        """Adapter returns same HonestJobs rows as aggregator search."""
        await _seed_honestjobs(db_session)
        await _seed_brightdata(db_session)

        from unittest.mock import patch
        from app.cities.config import CityConfig
        from app.integrations.adapters.honestjobs_adapter import HonestJobsJobAdapter
        from app.integrations.job_aggregator import JobAggregator

        adapter = HonestJobsJobAdapter()
        adapter_rows = await adapter.fetch_jobs(db_session, "jobs", "Montgomery, AL")

        cfg = CityConfig(
            name="Montgomery", state="AL", location="Montgomery, AL",
            zip_ranges=["36101-36120"], job_adapters=["brightdata", "honestjobs"],
            data_dir="data/cities/montgomery",
        )
        with patch("app.integrations.job_aggregator.get_city_config", return_value=cfg):
            agg = JobAggregator(db_session)
            agg_rows = await agg.search(source="honestjobs")

        assert len(adapter_rows) == len(agg_rows)
        adapter_sorted = sorted(adapter_rows, key=lambda r: r["title"])
        agg_sorted = sorted(agg_rows, key=lambda r: r["title"])
        for a, b in zip(adapter_sorted, agg_sorted):
            assert a == b


class TestHonestJobsAdapterProtocol:
    def test_satisfies_job_adapter_protocol(self):
        from app.integrations.adapters.base import JobAdapter
        from app.integrations.adapters.honestjobs_adapter import HonestJobsJobAdapter

        assert isinstance(HonestJobsJobAdapter(), JobAdapter)

    def test_registry_returns_adapter(self):
        from app.integrations.adapters.base import get_adapter, JobAdapter

        adapter = get_adapter("honestjobs")
        assert isinstance(adapter, JobAdapter)

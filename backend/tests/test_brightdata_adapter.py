"""Tests for BrightDataJobAdapter — wraps _brightdata_cached query logic."""

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


async def _seed_brightdata(session):
    listings = [
        _make_listing("CNA", "Baptist Health", "brightdata:snap-1",
                       location="Montgomery, AL"),
        _make_listing("Warehouse Worker", "Amazon", "brightdata:snap-2",
                       location="Montgomery, AL"),
        _make_listing("Cashier", "Dollar General", "brightdata:snap-1",
                       location="Montgomery, AL"),
    ]
    await insert_job_listings(session, listings)
    return listings


async def _seed_expired(session):
    await session.execute(
        text(
            "INSERT INTO job_listings "
            "(title, company, location, source, scraped_at, expires_at) "
            "VALUES (:title, :company, :location, :source, :scraped_at, :expires_at)"
        ),
        {
            "title": "Old Job",
            "company": "Gone LLC",
            "location": "Montgomery, AL",
            "source": "brightdata:snap-old",
            "scraped_at": "2020-01-01T00:00:00Z",
            "expires_at": "2020-02-01T00:00:00Z",
        },
    )
    await session.commit()


async def _seed_honestjobs(session):
    await session.execute(
        text(
            "INSERT INTO job_listings "
            "(title, company, location, source, scraped_at, expires_at) "
            "VALUES (:title, :company, :location, :source, :scraped_at, :expires_at)"
        ),
        {
            "title": "Forklift Op",
            "company": "Goodwill",
            "location": "Montgomery, AL",
            "source": "honestjobs",
            "scraped_at": "2026-03-08T00:00:00Z",
            "expires_at": "2099-12-31T00:00:00Z",
        },
    )
    await session.commit()


async def _seed_null_expiry(session):
    await session.execute(
        text(
            "INSERT INTO job_listings "
            "(title, company, location, source, scraped_at, expires_at) "
            "VALUES (:title, :company, :location, :source, :scraped_at, NULL)"
        ),
        {
            "title": "No Expiry Job",
            "company": "Permanent Co",
            "location": "Montgomery, AL",
            "source": "brightdata:snap-perm",
            "scraped_at": "2026-03-08T00:00:00Z",
        },
    )
    await session.commit()


class TestBrightDataAdapterFetchJobs:
    @pytest.mark.anyio
    async def test_returns_brightdata_rows(self, db_session):
        await _seed_brightdata(db_session)
        from app.integrations.adapters.brightdata_adapter import BrightDataJobAdapter

        adapter = BrightDataJobAdapter()
        rows = await adapter.fetch_jobs(db_session, "jobs", "Montgomery, AL")
        assert len(rows) == 3

    @pytest.mark.anyio
    async def test_excludes_expired_rows(self, db_session):
        await _seed_brightdata(db_session)
        await _seed_expired(db_session)
        from app.integrations.adapters.brightdata_adapter import BrightDataJobAdapter

        adapter = BrightDataJobAdapter()
        rows = await adapter.fetch_jobs(db_session, "jobs", "Montgomery, AL")
        assert len(rows) == 3
        titles = {r["title"] for r in rows}
        assert "Old Job" not in titles

    @pytest.mark.anyio
    async def test_excludes_non_brightdata_sources(self, db_session):
        await _seed_brightdata(db_session)
        await _seed_honestjobs(db_session)
        from app.integrations.adapters.brightdata_adapter import BrightDataJobAdapter

        adapter = BrightDataJobAdapter()
        rows = await adapter.fetch_jobs(db_session, "jobs", "Montgomery, AL")
        assert all(r["source"].startswith("brightdata:") for r in rows)

    @pytest.mark.anyio
    async def test_includes_null_expires_at(self, db_session):
        await _seed_null_expiry(db_session)
        from app.integrations.adapters.brightdata_adapter import BrightDataJobAdapter

        adapter = BrightDataJobAdapter()
        rows = await adapter.fetch_jobs(db_session, "jobs", "Montgomery, AL")
        assert len(rows) == 1
        assert rows[0]["title"] == "No Expiry Job"

    @pytest.mark.anyio
    async def test_returns_dicts(self, db_session):
        await _seed_brightdata(db_session)
        from app.integrations.adapters.brightdata_adapter import BrightDataJobAdapter

        adapter = BrightDataJobAdapter()
        rows = await adapter.fetch_jobs(db_session, "jobs", "Montgomery, AL")
        assert all(isinstance(r, dict) for r in rows)

    @pytest.mark.anyio
    async def test_empty_table_returns_empty_list(self, db_session):
        from app.integrations.adapters.brightdata_adapter import BrightDataJobAdapter

        adapter = BrightDataJobAdapter()
        rows = await adapter.fetch_jobs(db_session, "jobs", "Montgomery, AL")
        assert rows == []


class TestBrightDataAdapterMatchesAggregator:
    @pytest.mark.anyio
    async def test_byte_identical_to_aggregator(self, db_session):
        """Adapter returns same BrightData rows as aggregator search."""
        await _seed_brightdata(db_session)
        await _seed_expired(db_session)
        await _seed_honestjobs(db_session)

        from unittest.mock import patch
        from app.cities.config import CityConfig
        from app.integrations.adapters.brightdata_adapter import BrightDataJobAdapter
        from app.integrations.job_aggregator import JobAggregator

        adapter = BrightDataJobAdapter()
        adapter_rows = await adapter.fetch_jobs(db_session, "jobs", "Montgomery, AL")

        cfg = CityConfig(
            name="Montgomery", state="AL", location="Montgomery, AL",
            zip_ranges=["36101-36120"], job_adapters=["brightdata", "honestjobs"],
            data_dir="data/cities/montgomery",
        )
        with patch("app.integrations.job_aggregator.get_city_config", return_value=cfg):
            agg = JobAggregator(db_session)
            agg_rows = await agg.search(source="brightdata")

        assert len(adapter_rows) == len(agg_rows)
        adapter_sorted = sorted(adapter_rows, key=lambda r: r["title"])
        agg_sorted = sorted(agg_rows, key=lambda r: r["title"])
        for a, b in zip(adapter_sorted, agg_sorted):
            assert a == b


class TestBrightDataAdapterProtocol:
    def test_satisfies_job_adapter_protocol(self):
        from app.integrations.adapters.base import JobAdapter
        from app.integrations.adapters.brightdata_adapter import BrightDataJobAdapter

        assert isinstance(BrightDataJobAdapter(), JobAdapter)

    def test_registry_returns_adapter(self):
        from app.integrations.adapters.base import get_adapter, JobAdapter

        adapter = get_adapter("brightdata")
        assert isinstance(adapter, JobAdapter)

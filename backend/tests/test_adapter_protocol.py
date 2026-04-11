"""Tests for JobAdapter protocol, adapter registry, and BrightData round-trip."""

import pytest

from app.core.database import get_async_session_factory
from app.core.queries_jobs import insert_job_listings
from app.integrations.adapters.base import (
    AdapterNotFoundError,
    JobAdapter,
    get_adapter,
)


@pytest.fixture
async def db_session(test_engine):
    factory = get_async_session_factory()
    async with factory() as session:
        yield session


class TestRegistryLookup:
    def test_brightdata_returns_protocol_instance(self):
        adapter = get_adapter("brightdata")
        assert isinstance(adapter, JobAdapter)

    def test_honestjobs_returns_protocol_instance(self):
        adapter = get_adapter("honestjobs")
        assert isinstance(adapter, JobAdapter)

    def test_twc_returns_protocol_instance(self):
        adapter = get_adapter("twc")
        assert isinstance(adapter, JobAdapter)

    def test_usajobs_returns_protocol_instance(self):
        adapter = get_adapter("usajobs")
        assert isinstance(adapter, JobAdapter)


class TestUnknownAdapterRaises:
    def test_unknown_name_raises_adapter_not_found(self):
        with pytest.raises(AdapterNotFoundError):
            get_adapter("nonexistent")

    def test_error_includes_adapter_name(self):
        with pytest.raises(AdapterNotFoundError) as exc_info:
            get_adapter("bogus_adapter")
        assert "bogus_adapter" in str(exc_info.value)

    def test_error_stores_adapter_name_attr(self):
        with pytest.raises(AdapterNotFoundError) as exc_info:
            get_adapter("missing")
        assert exc_info.value.adapter_name == "missing"


def _make_listing(title, company, source, **kwargs):
    return {
        "title": title,
        "company": company,
        "source": source,
        "scraped_at": "2026-03-08T00:00:00Z",
        "expires_at": "2099-12-31T00:00:00Z",
        **kwargs,
    }


BRIGHTDATA_FIXTURE = [
    _make_listing("CNA", "Baptist Health", "brightdata:snap-1", location="Montgomery, AL"),
    _make_listing("Warehouse Worker", "Amazon", "brightdata:snap-2", location="Montgomery, AL"),
    _make_listing("Cashier", "Dollar General", "brightdata:snap-1", location="Montgomery, AL"),
]


class TestBrightDataRoundTrip:
    """Insert fixture data, fetch via adapter, verify round-trip fidelity."""

    @pytest.mark.anyio
    async def test_round_trips_all_fixture_rows(self, db_session):
        await insert_job_listings(db_session, BRIGHTDATA_FIXTURE)
        adapter = get_adapter("brightdata")
        rows = await adapter.fetch_jobs(db_session, "jobs", "Montgomery, AL")
        assert len(rows) == len(BRIGHTDATA_FIXTURE)

    @pytest.mark.anyio
    async def test_round_trip_preserves_titles(self, db_session):
        await insert_job_listings(db_session, BRIGHTDATA_FIXTURE)
        adapter = get_adapter("brightdata")
        rows = await adapter.fetch_jobs(db_session, "jobs", "Montgomery, AL")
        titles = {r["title"] for r in rows}
        expected = {f["title"] for f in BRIGHTDATA_FIXTURE}
        assert titles == expected

    @pytest.mark.anyio
    async def test_round_trip_preserves_companies(self, db_session):
        await insert_job_listings(db_session, BRIGHTDATA_FIXTURE)
        adapter = get_adapter("brightdata")
        rows = await adapter.fetch_jobs(db_session, "jobs", "Montgomery, AL")
        companies = {r["company"] for r in rows}
        expected = {f["company"] for f in BRIGHTDATA_FIXTURE}
        assert companies == expected

    @pytest.mark.anyio
    async def test_round_trip_preserves_sources(self, db_session):
        await insert_job_listings(db_session, BRIGHTDATA_FIXTURE)
        adapter = get_adapter("brightdata")
        rows = await adapter.fetch_jobs(db_session, "jobs", "Montgomery, AL")
        assert all(r["source"].startswith("brightdata:") for r in rows)

    @pytest.mark.anyio
    async def test_empty_db_returns_empty(self, db_session):
        adapter = get_adapter("brightdata")
        rows = await adapter.fetch_jobs(db_session, "jobs", "Montgomery, AL")
        assert rows == []

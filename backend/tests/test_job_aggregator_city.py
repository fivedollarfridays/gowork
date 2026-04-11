"""Tests for JobAggregator CITY selection — snapshot parity and multi-city behavior."""

from unittest.mock import patch

import pytest
from sqlalchemy import text

from app.cities.config import CityConfig
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


SNAPSHOT_FIXTURE = [
    _make_listing("CNA", "Baptist Health", "brightdata:snap-1", location="Montgomery, AL"),
    _make_listing("Warehouse Worker", "Amazon", "brightdata:snap-2", location="Montgomery, AL"),
    _make_listing("Cashier", "Dollar General", "brightdata:snap-1", location="Montgomery, AL"),
]

HONESTJOBS_FIXTURE = [
    {
        "title": "Forklift Operator",
        "company": "Goodwill",
        "location": "Montgomery, AL",
        "source": "honestjobs",
        "scraped_at": "2026-03-08T00:00:00Z",
        "expires_at": "2099-12-31T00:00:00Z",
        "fair_chance": 1,
    },
]

MONTGOMERY_CONFIG = CityConfig(
    name="Montgomery",
    state="AL",
    location="Montgomery, AL",
    zip_ranges=["36101-36120"],
    job_adapters=["brightdata", "honestjobs"],
    data_dir="data/cities/montgomery",
)

FORT_WORTH_CONFIG = CityConfig(
    name="Fort Worth",
    state="TX",
    location="Fort Worth, TX",
    zip_ranges=["76101-76199"],
    job_adapters=["twc", "usajobs"],
    data_dir="data/cities/fort-worth",
)


async def _seed_honestjobs(session):
    for listing in HONESTJOBS_FIXTURE:
        await session.execute(
            text(
                "INSERT INTO job_listings "
                "(title, company, location, source, scraped_at, expires_at, fair_chance) "
                "VALUES (:title, :company, :location, :source, :scraped_at, :expires_at, :fair_chance)"
            ),
            listing,
        )
    await session.commit()


class TestMontgomerySnapshotParity:
    """CITY=montgomery must produce output identical to pre-sprint JobAggregator.

    The snapshot fixture (SNAPSHOT_FIXTURE + HONESTJOBS_FIXTURE) represents
    the canonical pre-sprint output. Post-sprint code with CITY=montgomery
    must return the same rows — this is the backward-compat anchor.
    """

    @pytest.mark.anyio
    async def test_snapshot_row_count(self, db_session):
        await insert_job_listings(db_session, SNAPSHOT_FIXTURE)
        await _seed_honestjobs(db_session)

        from app.integrations.job_aggregator import JobAggregator

        with patch("app.integrations.job_aggregator.get_city_config", return_value=MONTGOMERY_CONFIG):
            agg = JobAggregator(db_session)
            results = await agg.search()

        assert len(results) == len(SNAPSHOT_FIXTURE) + len(HONESTJOBS_FIXTURE)

    @pytest.mark.anyio
    async def test_snapshot_titles_match(self, db_session):
        await insert_job_listings(db_session, SNAPSHOT_FIXTURE)
        await _seed_honestjobs(db_session)

        from app.integrations.job_aggregator import JobAggregator

        with patch("app.integrations.job_aggregator.get_city_config", return_value=MONTGOMERY_CONFIG):
            agg = JobAggregator(db_session)
            results = await agg.search()

        expected_titles = {f["title"] for f in SNAPSHOT_FIXTURE + HONESTJOBS_FIXTURE}
        actual_titles = {r["title"] for r in results}
        assert actual_titles == expected_titles

    @pytest.mark.anyio
    async def test_snapshot_sources_match(self, db_session):
        await insert_job_listings(db_session, SNAPSHOT_FIXTURE)
        await _seed_honestjobs(db_session)

        from app.integrations.job_aggregator import JobAggregator

        with patch("app.integrations.job_aggregator.get_city_config", return_value=MONTGOMERY_CONFIG):
            agg = JobAggregator(db_session)
            results = await agg.search()

        sources = {r["source"] for r in results}
        assert any(s.startswith("brightdata:") for s in sources)
        assert "honestjobs" in sources

    @pytest.mark.anyio
    async def test_snapshot_source_filter_brightdata(self, db_session):
        await insert_job_listings(db_session, SNAPSHOT_FIXTURE)
        await _seed_honestjobs(db_session)

        from app.integrations.job_aggregator import JobAggregator

        with patch("app.integrations.job_aggregator.get_city_config", return_value=MONTGOMERY_CONFIG):
            agg = JobAggregator(db_session)
            results = await agg.search(source="brightdata")

        assert len(results) == len(SNAPSHOT_FIXTURE)
        assert all(r["source"].startswith("brightdata:") for r in results)

    @pytest.mark.anyio
    async def test_snapshot_fair_chance_filter(self, db_session):
        await insert_job_listings(db_session, SNAPSHOT_FIXTURE)
        await _seed_honestjobs(db_session)

        from app.integrations.job_aggregator import JobAggregator

        with patch("app.integrations.job_aggregator.get_city_config", return_value=MONTGOMERY_CONFIG):
            agg = JobAggregator(db_session)
            results = await agg.search(fair_chance=True)

        assert len(results) == len(HONESTJOBS_FIXTURE)
        assert all(r.get("fair_chance") == 1 for r in results)

    @pytest.mark.anyio
    async def test_snapshot_search_signature_unchanged(self, db_session):
        """search() still accepts query, location, source, fair_chance kwargs."""
        from app.integrations.job_aggregator import JobAggregator

        with patch("app.integrations.job_aggregator.get_city_config", return_value=MONTGOMERY_CONFIG):
            agg = JobAggregator(db_session)
            results = await agg.search(
                query="jobs",
                location="Montgomery, AL",
                source=None,
                fair_chance=False,
            )

        assert isinstance(results, list)


class TestFortWorthReturnsEmpty:
    """CITY=fort-worth uses TWC+USAJobs stubs which return empty lists."""

    @pytest.mark.anyio
    async def test_fort_worth_returns_empty(self, db_session):
        from app.integrations.job_aggregator import JobAggregator

        with patch("app.integrations.job_aggregator.get_city_config", return_value=FORT_WORTH_CONFIG):
            agg = JobAggregator(db_session)
            results = await agg.search()

        assert results == []

    @pytest.mark.anyio
    async def test_fort_worth_ignores_montgomery_data(self, db_session):
        await insert_job_listings(db_session, SNAPSHOT_FIXTURE)
        await _seed_honestjobs(db_session)

        from app.integrations.job_aggregator import JobAggregator

        with patch("app.integrations.job_aggregator.get_city_config", return_value=FORT_WORTH_CONFIG):
            agg = JobAggregator(db_session)
            results = await agg.search()

        assert results == []

    @pytest.mark.anyio
    async def test_fort_worth_no_errors(self, db_session):
        from app.integrations.job_aggregator import JobAggregator

        with patch("app.integrations.job_aggregator.get_city_config", return_value=FORT_WORTH_CONFIG):
            agg = JobAggregator(db_session)
            results = await agg.search(query="warehouse", source=None, fair_chance=False)

        assert isinstance(results, list)

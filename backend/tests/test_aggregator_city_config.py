"""Tests for city-config-driven JobAggregator refactor (T1.6)."""

from unittest.mock import patch

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


async def _seed_brightdata(session, count=3):
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
    listings = [
        _make_listing("Forklift Operator", "Goodwill", "honestjobs",
                       location="Montgomery, AL"),
        _make_listing("Custodial Tech", "ABM Industries", "honestjobs",
                       location="Montgomery, AL"),
    ][:count]
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


class TestAggregatorMontgomeryDefault:
    """With CITY=montgomery (default), behavior is byte-identical to pre-sprint."""

    @pytest.mark.anyio
    async def test_montgomery_returns_brightdata_and_honestjobs(self, db_session):
        await _seed_brightdata(db_session, 2)
        await _seed_honestjobs(db_session, 1)
        from app.integrations.job_aggregator import JobAggregator

        with patch("app.integrations.job_aggregator.get_city_config") as mock_cfg:
            from app.cities.config import CityConfig

            mock_cfg.return_value = CityConfig(
                name="Montgomery", state="AL",
                zip_ranges=["36101-36120"], data_dir="data/cities/montgomery",
                job_adapters=["brightdata", "honestjobs"],
                location="Montgomery, AL",
            )
            agg = JobAggregator(db_session)
            results = await agg.search()
        assert len(results) == 3

    @pytest.mark.anyio
    async def test_montgomery_search_signature_preserved(self, db_session):
        """search() still accepts query, location, source, fair_chance kwargs."""
        from app.integrations.job_aggregator import JobAggregator

        with patch("app.integrations.job_aggregator.get_city_config") as mock_cfg:
            from app.cities.config import CityConfig

            mock_cfg.return_value = CityConfig(
                name="Montgomery", state="AL",
                zip_ranges=["36101-36120"], data_dir="data/cities/montgomery",
                job_adapters=["brightdata", "honestjobs"],
                location="Montgomery, AL",
            )
            agg = JobAggregator(db_session)
            results = await agg.search(
                query="jobs", location="Montgomery, AL",
                source=None, fair_chance=False,
            )
        assert isinstance(results, list)


class TestAggregatorFortWorth:
    """With CITY=fort-worth, stubs return [] and no errors."""

    @pytest.mark.anyio
    async def test_fort_worth_returns_empty(self, db_session):
        from app.integrations.job_aggregator import JobAggregator

        with patch("app.integrations.job_aggregator.get_city_config") as mock_cfg:
            from app.cities.config import CityConfig

            mock_cfg.return_value = CityConfig(
                name="Fort Worth", state="TX",
                zip_ranges=["76101-76199"], data_dir="data/cities/fort-worth",
                job_adapters=["twc", "usajobs"],
                location="Fort Worth, TX",
            )
            agg = JobAggregator(db_session)
            results = await agg.search()
        assert results == []

    @pytest.mark.anyio
    async def test_fort_worth_does_not_error(self, db_session):
        from app.integrations.job_aggregator import JobAggregator

        with patch("app.integrations.job_aggregator.get_city_config") as mock_cfg:
            from app.cities.config import CityConfig

            mock_cfg.return_value = CityConfig(
                name="Fort Worth", state="TX",
                zip_ranges=["76101-76199"], data_dir="data/cities/fort-worth",
                job_adapters=["twc", "usajobs"],
                location="Fort Worth, TX",
            )
            agg = JobAggregator(db_session)
            results = await agg.search(query="warehouse", source=None, fair_chance=False)
        assert isinstance(results, list)


class TestAggregatorLocationFromConfig:
    """Default location comes from city config, not hardcoded."""

    @pytest.mark.anyio
    async def test_location_default_from_config(self, db_session):
        """search() uses city config location as default, not 'Montgomery, AL'."""
        import inspect
        from app.integrations.job_aggregator import JobAggregator

        sig = inspect.signature(JobAggregator.search)
        loc_param = sig.parameters.get("location")
        assert loc_param is not None
        assert loc_param.default is None or loc_param.default == inspect.Parameter.empty


class TestAggregatorNoHardcodedAdapters:
    """Aggregator must not have hardcoded _brightdata_cached / _honestjobs_cached."""

    def test_no_brightdata_cached_method(self):
        from app.integrations.job_aggregator import JobAggregator

        assert not hasattr(JobAggregator, "_brightdata_cached")

    def test_no_honestjobs_cached_method(self):
        from app.integrations.job_aggregator import JobAggregator

        assert not hasattr(JobAggregator, "_honestjobs_cached")

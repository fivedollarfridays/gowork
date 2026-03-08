"""Tests for BrightData post-crawl exclusion filter."""

import pytest

from app.core.database import get_async_session_factory
from app.core.queries_jobs import get_job_listings_by_source
from app.integrations.brightdata.cache import _should_exclude, store_crawl_results


@pytest.fixture
async def db_session(test_engine):
    factory = get_async_session_factory()
    async with factory() as session:
        yield session


class TestShouldExclude:
    """Title and salary exclusion filter tests."""

    def test_excludes_ceo(self):
        assert _should_exclude({"title": "CEO of Operations"}) is True

    def test_excludes_cfo(self):
        assert _should_exclude({"title": "CFO"}) is True

    def test_excludes_cto(self):
        assert _should_exclude({"title": "CTO - Tech Startup"}) is True

    def test_excludes_coo(self):
        assert _should_exclude({"title": "COO"}) is True

    def test_excludes_vp(self):
        assert _should_exclude({"title": "VP of Sales"}) is True

    def test_excludes_vice_president(self):
        assert _should_exclude({"title": "Vice President Marketing"}) is True

    def test_excludes_director(self):
        assert _should_exclude({"title": "Director of Engineering"}) is True

    def test_excludes_managing_director(self):
        assert _should_exclude({"title": "Managing Director"}) is True

    def test_excludes_attorney(self):
        assert _should_exclude({"title": "Attorney at Law"}) is True

    def test_excludes_physician(self):
        assert _should_exclude({"title": "Physician - Internal Medicine"}) is True

    def test_excludes_surgeon(self):
        assert _should_exclude({"title": "Surgeon"}) is True

    def test_excludes_partner(self):
        assert _should_exclude({"title": "Partner, Law Firm"}) is True

    def test_excludes_chief(self):
        assert _should_exclude({"title": "Chief Marketing Officer"}) is True

    def test_keeps_normal_jobs(self):
        assert _should_exclude({"title": "Warehouse Worker"}) is False
        assert _should_exclude({"title": "CNA"}) is False
        assert _should_exclude({"title": "Cashier"}) is False
        assert _should_exclude({"title": "Customer Service Rep"}) is False

    def test_case_insensitive_title(self):
        assert _should_exclude({"title": "vp of sales"}) is True
        assert _should_exclude({"title": "DIRECTOR of HR"}) is True

    def test_excludes_high_salary_yearly(self):
        assert _should_exclude({"title": "Analyst", "salary": "$90,000/yr"}) is True
        assert _should_exclude({"title": "Analyst", "salary": "$85,000/year"}) is True

    def test_keeps_moderate_salary_yearly(self):
        assert _should_exclude({"title": "Analyst", "salary": "$45,000/yr"}) is False
        assert _should_exclude({"title": "Analyst", "salary": "$80,000/yr"}) is False

    def test_excludes_high_salary_hourly(self):
        assert _should_exclude({"title": "Consultant", "salary": "$45/hr"}) is True

    def test_keeps_moderate_salary_hourly(self):
        assert _should_exclude({"title": "Clerk", "salary": "$20/hr"}) is False

    def test_handles_missing_salary(self):
        assert _should_exclude({"title": "Worker"}) is False

    def test_handles_empty_salary(self):
        assert _should_exclude({"title": "Worker", "salary": ""}) is False

    def test_handles_unparseable_salary(self):
        assert _should_exclude({"title": "Worker", "salary": "competitive"}) is False

    def test_handles_missing_title(self):
        assert _should_exclude({}) is False
        assert _should_exclude({"salary": "$90,000/yr"}) is False

    def test_no_false_positive_on_service_director(self):
        assert _should_exclude({"title": "Directing Traffic Control"}) is False


class TestStoreCrawlResultsExclusion:
    """Verify exclusion filter is applied during store."""

    @pytest.mark.anyio
    async def test_excludes_executive_titles(self, db_session):
        raw = [
            {"title": "CEO", "url": "https://example.com/ceo"},
            {"title": "Cashier", "url": "https://example.com/cashier"},
        ]
        count = await store_crawl_results(db_session, "snap-excl", raw)
        assert count == 1
        results = await get_job_listings_by_source(db_session, "brightdata:snap-excl")
        assert results[0]["title"] == "Cashier"

    @pytest.mark.anyio
    async def test_excludes_high_salary(self, db_session):
        raw = [
            {"title": "Analyst", "salary": "$95,000/yr", "url": "https://example.com/a"},
            {"title": "Clerk", "salary": "$30,000/yr", "url": "https://example.com/c"},
        ]
        count = await store_crawl_results(db_session, "snap-sal", raw)
        assert count == 1

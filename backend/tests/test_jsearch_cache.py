"""Tests for JSearch job listing cache — parse, dedup, insert."""

import pytest
from sqlalchemy import text

from app.core.database import get_async_session_factory
from app.core.queries_jobs import get_job_listings_by_source
from app.integrations.jsearch.cache import (
    normalize_period,
    parse_jsearch_jobs,
    store_jsearch_results,
)


@pytest.fixture
async def db_session(test_engine):
    """Yield an async session from the test engine."""
    factory = get_async_session_factory()
    async with factory() as session:
        yield session


SAMPLE_JSEARCH_JOBS = [
    {
        "job_title": "Warehouse Associate",
        "employer_name": "Amazon",
        "job_city": "Montgomery",
        "job_state": "AL",
        "job_description": "Pack and ship orders in warehouse facility",
        "job_apply_link": "https://amazon.com/apply/warehouse",
        "job_min_salary": 15.0,
        "job_max_salary": 18.0,
        "job_salary_period": "HOUR",
        "job_employment_type": "FULLTIME",
    },
    {
        "job_title": "Delivery Driver",
        "employer_name": "FedEx",
        "job_city": "Montgomery",
        "job_state": "AL",
        "job_description": "Deliver packages to residential addresses",
        "job_apply_link": "https://fedex.com/apply/driver",
        "job_min_salary": 16.0,
        "job_max_salary": 20.0,
        "job_salary_period": "HOUR",
        "job_employment_type": "FULLTIME",
    },
]


class TestParseJSearchJobs:
    def test_parses_valid_jobs(self):
        result = parse_jsearch_jobs(SAMPLE_JSEARCH_JOBS)
        assert len(result) == 2
        assert result[0].title == "Warehouse Associate"
        assert result[0].company == "Amazon"
        assert result[0].location == "Montgomery, AL"
        assert result[0].url == "https://amazon.com/apply/warehouse"

    def test_handles_missing_optional_fields(self):
        raw = [{"job_title": "Cashier"}]
        result = parse_jsearch_jobs(raw)
        assert len(result) == 1
        assert result[0].company is None
        assert result[0].url is None

    def test_skips_records_without_title(self):
        raw = [{"employer_name": "Acme"}, {"job_title": "Valid Job"}]
        result = parse_jsearch_jobs(raw)
        assert len(result) == 1
        assert result[0].title == "Valid Job"

    def test_empty_list_returns_empty(self):
        assert parse_jsearch_jobs([]) == []

    def test_excludes_executive_titles(self):
        raw = [
            {"job_title": "CEO of Operations"},
            {"job_title": "VP Sales"},
            {"job_title": "Director of Engineering"},
            {"job_title": "Warehouse Worker"},
        ]
        result = parse_jsearch_jobs(raw)
        assert len(result) == 1
        assert result[0].title == "Warehouse Worker"

    def test_excludes_high_salary_hourly(self):
        raw = [{"job_title": "Consultant", "job_max_salary": 50.0,
                "job_salary_period": "HOUR"}]
        result = parse_jsearch_jobs(raw)
        assert len(result) == 0  # $50/hr * 2080 = $104k > $80k

    def test_excludes_high_salary_annual(self):
        raw = [{"job_title": "Engineer", "job_max_salary": 90000.0,
                "job_salary_period": "YEAR"}]
        result = parse_jsearch_jobs(raw)
        assert len(result) == 0

    def test_keeps_reasonable_salary(self):
        raw = [{"job_title": "Driver", "job_max_salary": 18.0,
                "job_salary_period": "HOUR"}]
        result = parse_jsearch_jobs(raw)
        assert len(result) == 1

    def test_builds_location_from_city_state(self):
        raw = [{"job_title": "Job", "job_city": "Birmingham", "job_state": "AL"}]
        result = parse_jsearch_jobs(raw)
        assert result[0].location == "Birmingham, AL"

    def test_location_with_only_city(self):
        raw = [{"job_title": "Job", "job_city": "Montgomery"}]
        result = parse_jsearch_jobs(raw)
        assert result[0].location == "Montgomery"

    def test_location_with_only_state(self):
        raw = [{"job_title": "Job", "job_state": "AL"}]
        result = parse_jsearch_jobs(raw)
        assert result[0].location == "AL"


class TestNormalizePeriod:
    def test_year_returns_annual(self):
        assert normalize_period("YEAR") == "annual"

    def test_yearly_returns_annual(self):
        assert normalize_period("YEARLY") == "annual"

    def test_annual_returns_annual(self):
        assert normalize_period("ANNUAL") == "annual"

    def test_unknown_period_lowercased(self):
        assert normalize_period("MONTHLY") == "monthly"


class TestFieldTruncation:
    def test_truncates_long_title(self):
        raw = [{"job_title": "A" * 1000}]
        result = parse_jsearch_jobs(raw)
        assert len(result[0].title) == 500

    def test_truncates_long_company(self):
        raw = [{"job_title": "Job", "employer_name": "B" * 500}]
        result = parse_jsearch_jobs(raw)
        assert len(result[0].company) == 200

    def test_truncates_long_description(self):
        raw = [{"job_title": "Job", "job_description": "D" * 10000}]
        result = parse_jsearch_jobs(raw)
        assert len(result[0].description) == 5000

    def test_truncates_long_url(self):
        raw = [{"job_title": "Job", "job_apply_link": "https://x.com/" + "a" * 3000}]
        result = parse_jsearch_jobs(raw)
        assert len(result[0].url) == 2000


class TestStoreJSearchResults:
    @pytest.mark.anyio
    async def test_stores_parsed_jobs(self, db_session):
        count = await store_jsearch_results(
            db_session, "req-abc-123", SAMPLE_JSEARCH_JOBS,
        )
        assert count == 2
        results = await get_job_listings_by_source(db_session, "jsearch:req-abc-123")
        assert len(results) == 2

    @pytest.mark.anyio
    async def test_deduplicates_by_url(self, db_session):
        await store_jsearch_results(db_session, "req-1", SAMPLE_JSEARCH_JOBS)
        count = await store_jsearch_results(db_session, "req-2", SAMPLE_JSEARCH_JOBS)
        assert count == 0  # All URLs already exist

    @pytest.mark.anyio
    async def test_jobs_without_url_not_deduplicated(self, db_session):
        raw = [{"job_title": "CNA"}]
        await store_jsearch_results(db_session, "req-1", raw)
        count = await store_jsearch_results(db_session, "req-2", raw)
        assert count == 1  # No URL, no dedup

    @pytest.mark.anyio
    async def test_sets_24h_expiry(self, db_session):
        raw = [{"job_title": "Job", "job_apply_link": "https://example.com/exp"}]
        await store_jsearch_results(db_session, "req-exp", raw)
        result = await db_session.execute(
            text("SELECT scraped_at, expires_at FROM job_listings WHERE source = :s"),
            {"s": "jsearch:req-exp"},
        )
        row = result.first()
        assert row is not None
        assert row[1] > row[0]  # expires_at after scraped_at

    @pytest.mark.anyio
    async def test_skips_invalid_records(self, db_session):
        raw = [{"employer_name": "No Title"}, {"job_title": "Valid"}]
        count = await store_jsearch_results(db_session, "req-skip", raw)
        assert count == 1

    @pytest.mark.anyio
    async def test_all_invalid_returns_zero(self, db_session):
        raw = [{"employer_name": "No Title"}, {"job_description": "Also no title"}]
        count = await store_jsearch_results(db_session, "req-none", raw)
        assert count == 0

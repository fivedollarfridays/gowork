"""Tests for Honest Jobs fair-chance feed — schema, seed, client."""

import json
from unittest.mock import patch

import pytest
from sqlalchemy import text

from app.core.database import get_async_session_factory
from app.core.queries_jobs import get_job_listings_by_source
from app.integrations.honestjobs.client import HonestJobsClient
from app.integrations.honestjobs.seed import seed_honestjobs_listings


@pytest.fixture
async def db_session(test_engine):
    """Yield an async session from the test engine."""
    factory = get_async_session_factory()
    async with factory() as session:
        yield session


class TestFairChanceSchema:
    @pytest.mark.anyio
    async def test_fair_chance_column_exists(self, db_session):
        """The job_listings table should have a fair_chance column."""
        result = await db_session.execute(text("PRAGMA table_info(job_listings)"))
        columns = {row[1] for row in result}
        assert "fair_chance" in columns

    @pytest.mark.anyio
    async def test_fair_chance_defaults_to_zero(self, db_session):
        """fair_chance should default to 0 for new inserts."""
        await db_session.execute(
            text(
                "INSERT INTO job_listings (title, scraped_at) "
                "VALUES (:title, :scraped_at)"
            ),
            {"title": "Test Job", "scraped_at": "2026-03-08T00:00:00Z"},
        )
        await db_session.commit()
        result = await db_session.execute(
            text("SELECT fair_chance FROM job_listings WHERE title = 'Test Job'")
        )
        assert result.scalar() == 0


class TestSeedHonestJobsListings:
    @pytest.mark.anyio
    async def test_seeds_minimum_listings(self, db_session):
        """Should seed at least 10 Honest Jobs listings."""
        count = await seed_honestjobs_listings(db_session)
        assert count >= 10

    @pytest.mark.anyio
    async def test_all_seeded_have_honestjobs_source(self, db_session):
        """All seeded listings should have source = 'honestjobs'."""
        await seed_honestjobs_listings(db_session)
        results = await get_job_listings_by_source(db_session, "honestjobs")
        assert len(results) >= 10
        for job in results:
            assert job["source"] == "honestjobs"

    @pytest.mark.anyio
    async def test_all_seeded_have_fair_chance_flag(self, db_session):
        """All Honest Jobs listings should have fair_chance = 1."""
        await seed_honestjobs_listings(db_session)
        result = await db_session.execute(
            text(
                "SELECT fair_chance FROM job_listings "
                "WHERE source = 'honestjobs'"
            )
        )
        flags = [row[0] for row in result]
        assert all(f == 1 for f in flags)

    @pytest.mark.anyio
    async def test_idempotent_seeding(self, db_session):
        """Running seed twice should not create duplicates."""
        count1 = await seed_honestjobs_listings(db_session)
        count2 = await seed_honestjobs_listings(db_session)
        assert count1 >= 10
        assert count2 == 0  # All already exist

    @pytest.mark.anyio
    async def test_seeded_jobs_have_required_fields(self, db_session):
        """All seeded jobs should have title, company, location."""
        await seed_honestjobs_listings(db_session)
        results = await get_job_listings_by_source(db_session, "honestjobs")
        for job in results:
            assert job["title"], f"Missing title: {job}"
            assert job["company"], f"Missing company: {job}"
            assert job["location"], f"Missing location: {job}"


class TestSeedEdgeCases:
    @pytest.mark.anyio
    async def test_returns_zero_when_file_missing(self, db_session):
        """Returns 0 when seed file does not exist (lines 23-24)."""
        with patch("app.integrations.honestjobs.seed.Path.exists", return_value=False):
            count = await seed_honestjobs_listings(db_session)
        assert count == 0

    @pytest.mark.anyio
    async def test_returns_zero_when_data_empty(self, db_session):
        """Returns 0 when seed file contains empty list (line 28)."""
        with patch("app.integrations.honestjobs.seed.Path.exists", return_value=True), \
             patch("app.integrations.honestjobs.seed.Path.read_text", return_value="[]"):
            count = await seed_honestjobs_listings(db_session)
        assert count == 0


class TestSeedDataFile:
    def test_seed_file_is_valid_json(self):
        """Seed data file should be valid JSON."""
        from pathlib import Path
        data_dir = Path(__file__).parent.parent / "data"
        filepath = data_dir / "honestjobs_listings.json"
        assert filepath.exists(), f"Seed file missing: {filepath}"
        data = json.loads(filepath.read_text())
        assert isinstance(data, list)
        assert len(data) >= 10

    def test_seed_records_have_required_keys(self):
        """Each seed record should have title, company, location, source."""
        from pathlib import Path
        data_dir = Path(__file__).parent.parent / "data"
        data = json.loads((data_dir / "honestjobs_listings.json").read_text())
        for record in data:
            assert "title" in record
            assert "company" in record
            assert "location" in record
            assert record.get("source") == "honestjobs"
            assert record.get("fair_chance") == 1


class TestHonestJobsClient:
    @pytest.mark.anyio
    async def test_get_listings_returns_seeded_data(self, db_session):
        """get_listings() should return seeded Honest Jobs listings."""
        await seed_honestjobs_listings(db_session)
        client = HonestJobsClient(db_session)
        listings = await client.get_listings()
        assert len(listings) >= 10

    @pytest.mark.anyio
    async def test_get_listings_empty_when_not_seeded(self, db_session):
        """get_listings() should return empty list when nothing seeded."""
        client = HonestJobsClient(db_session)
        listings = await client.get_listings()
        assert listings == []

    @pytest.mark.anyio
    async def test_get_fair_chance_listings(self, db_session):
        """get_fair_chance_listings() returns only fair_chance=1 jobs."""
        await seed_honestjobs_listings(db_session)
        client = HonestJobsClient(db_session)
        listings = await client.get_fair_chance_listings()
        assert len(listings) >= 10
        for job in listings:
            assert job["fair_chance"] == 1

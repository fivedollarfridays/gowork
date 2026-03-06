"""Tests for job_listings seed data and credit_check column."""

import json

import pytest
from sqlalchemy import text

from app.core import database as db_module


class TestJobListingsDDL:
    """Verify the credit_check column exists on job_listings table."""

    @pytest.mark.anyio
    async def test_credit_check_column_exists(self, test_engine):
        """job_listings table should have a credit_check TEXT column."""
        async with test_engine.begin() as conn:
            result = await conn.execute(text("PRAGMA table_info(job_listings)"))
            columns = {row[1]: row[2] for row in result}
        assert "credit_check" in columns
        assert columns["credit_check"] == "TEXT"


class TestJobListingsSeed:
    """Verify job_listings.json is loaded by the seed loader."""

    @pytest.mark.anyio
    async def test_seed_file_map_includes_job_listings(self):
        """_seed_file_map should include job_listings.json -> job_listings."""
        entries = db_module._seed_file_map()
        tables = {table for _, table in entries}
        assert "job_listings" in tables

    @pytest.mark.anyio
    async def test_job_listings_allowed_columns(self):
        """ALLOWED_COLUMNS should include job_listings with credit_check."""
        assert "job_listings" in db_module.ALLOWED_COLUMNS
        assert "credit_check" in db_module.ALLOWED_COLUMNS["job_listings"]
        assert "title" in db_module.ALLOWED_COLUMNS["job_listings"]

    @pytest.mark.anyio
    async def test_seeds_load_job_listings(self, test_engine):
        """init_db should populate job_listings from data/job_listings.json."""
        async with test_engine.begin() as conn:
            result = await conn.execute(text("SELECT COUNT(*) FROM job_listings"))
            count = result.scalar()
        assert count >= 25, f"Expected at least 25 job listings, got {count}"

    @pytest.mark.anyio
    async def test_seeded_jobs_have_credit_check(self, test_engine):
        """Every seeded job listing should have a credit_check value."""
        valid_values = {"required", "not_required", "unknown"}
        async with test_engine.begin() as conn:
            result = await conn.execute(
                text("SELECT credit_check FROM job_listings")
            )
            values = [row[0] for row in result]
        assert len(values) > 0
        for val in values:
            assert val in valid_values, f"Invalid credit_check: {val}"

    @pytest.mark.anyio
    async def test_seeded_jobs_have_industry_mix(self, test_engine):
        """Seed data should include healthcare, manufacturing, government, retail, food_service."""
        async with test_engine.begin() as conn:
            result = await conn.execute(
                text("SELECT company FROM job_listings")
            )
            companies = [row[0] for row in result if row[0]]
        company_text = " ".join(companies).lower()
        # Check for at least some known Montgomery employers
        assert any(
            name in company_text
            for name in ["baptist", "jackson hospital", "hyundai"]
        ), f"Missing expected Montgomery employers in: {companies[:5]}..."

    @pytest.mark.anyio
    async def test_seeded_jobs_have_shift_variety(self, test_engine):
        """Seed data should include different shift types in descriptions."""
        async with test_engine.begin() as conn:
            result = await conn.execute(
                text("SELECT description FROM job_listings")
            )
            descriptions = [row[0] for row in result if row[0]]
        all_text = " ".join(descriptions).lower()
        # Should mention various shifts
        assert "night" in all_text or "evening" in all_text
        assert "day" in all_text or "morning" in all_text

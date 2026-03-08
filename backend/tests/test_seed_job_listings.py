"""Tests for job_listings table schema and seed configuration."""

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
    """Verify job_listings seed configuration (seed file is empty; data comes from BrightData)."""

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
    async def test_empty_seed_creates_no_rows(self, test_engine):
        """Empty job_listings.json should result in zero seeded rows."""
        async with test_engine.begin() as conn:
            result = await conn.execute(text("SELECT COUNT(*) FROM job_listings"))
            count = result.scalar()
        assert count == 0

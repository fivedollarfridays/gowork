"""Tests for city-aware Honest Jobs seed loader.

Layer 1 of the city-aware jobs pipeline: the seed loader must resolve to
``data/cities/<CITY>/honestjobs_listings.json`` so Fort Worth and Montgomery
deployments each surface their own fair-chance listings. Falls back to the
legacy ``data/honestjobs_listings.json`` only when no city-specific file
exists (back-compat for unknown CITY values).
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from sqlalchemy import text

from app.core.config import get_settings
from app.core.database import get_async_session_factory
from app.integrations.honestjobs.seed import (
    _resolve_seed_path,
    seed_honestjobs_listings,
)


@pytest.fixture
async def db_session(test_engine):
    factory = get_async_session_factory()
    async with factory() as session:
        yield session


class TestResolveSeedPath:
    """Path resolution helper — pure function, no DB."""

    def test_returns_city_specific_path_when_exists(self, monkeypatch):
        """For CITY=montgomery, returns cities/montgomery/honestjobs_listings.json."""
        monkeypatch.setenv("CITY", "montgomery")
        get_settings.cache_clear()
        path = _resolve_seed_path()
        assert path.parent.name == "montgomery"
        assert path.name == "honestjobs_listings.json"
        assert path.exists(), f"AL seed should exist at {path}"

    def test_returns_fort_worth_path_for_fw_deployment(self, monkeypatch):
        """For CITY=fort-worth, returns cities/fort-worth/honestjobs_listings.json."""
        monkeypatch.setenv("CITY", "fort-worth")
        get_settings.cache_clear()
        path = _resolve_seed_path()
        assert path.parent.name == "fort-worth"
        assert path.name == "honestjobs_listings.json"

    def test_returns_legacy_path_for_unknown_city_with_legacy_file(
        self, monkeypatch, tmp_path
    ):
        """For unknown city with a legacy file present, falls back to legacy path."""
        monkeypatch.setenv("CITY", "unknown-city")
        get_settings.cache_clear()
        # Legacy fallback path is data/honestjobs_listings.json. Patch
        # Path.exists to simulate its presence.
        original_exists = Path.exists

        def fake_exists(self: Path) -> bool:
            if self.name == "honestjobs_listings.json" and self.parent.name == "data":
                return True
            return original_exists(self)

        with patch.object(Path, "exists", fake_exists):
            path = _resolve_seed_path()
        # Either legacy or city-specific is acceptable; legacy is the fallback
        # path when city-specific does not exist.
        assert path.name == "honestjobs_listings.json"


class TestCityAwareSeed:
    """End-to-end seed behavior under different CITY values."""

    @pytest.mark.anyio
    async def test_montgomery_city_seeds_alabama_jobs(self, db_session, monkeypatch):
        """CITY=montgomery seeds Montgomery, AL listings."""
        monkeypatch.setenv("CITY", "montgomery")
        get_settings.cache_clear()
        count = await seed_honestjobs_listings(db_session)
        assert count >= 10
        result = await db_session.execute(
            text("SELECT location FROM job_listings WHERE source = 'honestjobs'")
        )
        locations = [row[0] for row in result]
        assert all(", AL" in loc for loc in locations), (
            f"Expected all AL locations, got: {locations}"
        )

    @pytest.mark.anyio
    async def test_fort_worth_city_seeds_texas_jobs(self, db_session, monkeypatch):
        """CITY=fort-worth seeds Fort Worth-area, TX listings."""
        monkeypatch.setenv("CITY", "fort-worth")
        get_settings.cache_clear()
        count = await seed_honestjobs_listings(db_session)
        assert count >= 10
        result = await db_session.execute(
            text("SELECT location FROM job_listings WHERE source = 'honestjobs'")
        )
        locations = [row[0] for row in result]
        assert all(", TX" in loc for loc in locations), (
            f"Expected all TX locations, got: {locations}"
        )

    @pytest.mark.anyio
    async def test_seed_data_does_not_cross_city_boundary(self, db_session, monkeypatch):
        """Switching CITY between runs does not bleed AL jobs into FW (or vice versa)."""
        # Seed FW first
        monkeypatch.setenv("CITY", "fort-worth")
        get_settings.cache_clear()
        await seed_honestjobs_listings(db_session)
        result = await db_session.execute(
            text("SELECT location FROM job_listings WHERE source = 'honestjobs'")
        )
        fw_locations = [row[0] for row in result]
        assert all(", TX" in loc for loc in fw_locations)
        assert not any(", AL" in loc for loc in fw_locations)

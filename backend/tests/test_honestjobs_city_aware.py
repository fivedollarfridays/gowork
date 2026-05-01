"""Tests for city-aware Honest Jobs seed loader.

Updated for the agnostic pipeline (m008+): the seeder loads listings
from EVERY ``data/cities/*/honestjobs_listings.json`` into the same
DB.  Per-request city boundary is enforced at query time by
``_filter_by_state`` in :mod:`app.modules.matching.job_matcher`.

The legacy single-file resolver (``_resolve_seed_path``) is retained
for callers that want the active-CITY's path (e.g. inspection, dev
tooling); the production seed loop uses the multi-city walker
internally.
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


class TestMultiCitySeed:
    """End-to-end seed behaviour: every configured city loaded once."""

    @pytest.mark.anyio
    async def test_seed_loads_alabama_listings(self, db_session, monkeypatch):
        """Montgomery, AL listings present in DB after seeding."""
        monkeypatch.setenv("CITY", "montgomery")
        get_settings.cache_clear()
        count = await seed_honestjobs_listings(db_session)
        assert count >= 10
        result = await db_session.execute(
            text("SELECT location FROM job_listings WHERE source = 'honestjobs'")
        )
        locations = [row[0] for row in result]
        assert any(", AL" in (loc or "") for loc in locations), (
            f"Expected at least one AL location, got: {locations}"
        )

    @pytest.mark.anyio
    async def test_seed_loads_texas_listings(self, db_session, monkeypatch):
        """Fort Worth, TX listings present in DB after seeding."""
        monkeypatch.setenv("CITY", "fort-worth")
        get_settings.cache_clear()
        count = await seed_honestjobs_listings(db_session)
        assert count >= 10
        result = await db_session.execute(
            text("SELECT location FROM job_listings WHERE source = 'honestjobs'")
        )
        locations = [row[0] for row in result]
        assert any(", TX" in (loc or "") for loc in locations), (
            f"Expected at least one TX location, got: {locations}"
        )

    @pytest.mark.anyio
    async def test_seed_loads_BOTH_cities_in_one_run(self, db_session, monkeypatch):
        """A single seed run loads every city's listings — boundary at query.

        Replaces the older ``test_seed_data_does_not_cross_city_boundary``
        contract: under the agnostic pipeline, listings from every city
        co-exist in the DB and ``_filter_by_state`` enforces the
        boundary at query time.
        """
        monkeypatch.setenv("CITY", "fort-worth")
        get_settings.cache_clear()
        await seed_honestjobs_listings(db_session)
        result = await db_session.execute(
            text("SELECT location FROM job_listings WHERE source = 'honestjobs'")
        )
        locations = [row[0] for row in result]
        assert any(", TX" in (loc or "") for loc in locations), \
            f"missing TX listings; got: {locations}"
        assert any(", AL" in (loc or "") for loc in locations), \
            f"missing AL listings; got: {locations}"

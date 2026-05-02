"""Tests for the FW resources/jobs geocoding backfill script.

The backfill script is the durable bridge between Mapbox-the-API and
``backend/data/cities/fort-worth/resources.json`` — the seed file that
survives DB rebuilds. We test the inner functions directly rather than
shelling out, which keeps the test fast and deterministic.

The geocoder itself is mocked: this test verifies the backfill loop's
contract (idempotent, persists results, counts successes / failures,
respects rate limit hook), not the network call.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest


# ---------- Per-resource decision logic ----------------------------


class TestNeedsGeocode:
    """``needs_geocode`` is the idempotency gate."""

    def test_skip_when_lat_and_lng_present(self):
        from scripts.backfill_geocode_fw_data import needs_geocode

        assert not needs_geocode(
            {"address": "100 Main St", "lat": 32.7, "lng": -97.3},
        )

    def test_geocode_when_lat_missing(self):
        from scripts.backfill_geocode_fw_data import needs_geocode

        assert needs_geocode({"address": "100 Main St", "lng": -97.3})

    def test_geocode_when_lng_null(self):
        from scripts.backfill_geocode_fw_data import needs_geocode

        assert needs_geocode(
            {"address": "100 Main St", "lat": 32.7, "lng": None},
        )

    def test_skip_when_no_address(self):
        """Without an address, we can't geocode — leave alone."""
        from scripts.backfill_geocode_fw_data import needs_geocode

        assert not needs_geocode({"address": None, "lat": None})
        assert not needs_geocode({"lat": None})


# ---------- Resources-file loop ------------------------------------


class TestResourceBackfill:
    """``backfill_resources_file`` walks the JSON, geocodes nulls,
    persists, and reports counts."""

    @pytest.mark.asyncio
    async def test_processes_only_missing_rows(self, tmp_path):
        from scripts.backfill_geocode_fw_data import backfill_resources_file

        resources = [
            {"name": "A", "address": "1 A St", "lat": 32.0, "lng": -97.0},
            {"name": "B", "address": "2 B St", "lat": None, "lng": None},
            {"name": "C", "address": None, "lat": None, "lng": None},
        ]
        path = tmp_path / "resources.json"
        path.write_text(json.dumps(resources), encoding="utf-8")

        async def fake_geocode(addr: str):
            return (32.5, -97.5)

        with patch(
            "scripts.backfill_geocode_fw_data.geocode_address",
            new=AsyncMock(side_effect=fake_geocode),
        ) as mock_geo:
            result = await backfill_resources_file(
                str(path), rate_limit_seconds=0,
            )

        # Only "B" needs geocoding ("A" is done, "C" has no address).
        assert mock_geo.await_count == 1
        assert result.geocoded == 1
        assert result.failed == 0
        assert result.skipped == 2

        persisted = json.loads(path.read_text(encoding="utf-8"))
        assert persisted[0]["lat"] == 32.0  # untouched
        assert persisted[1]["lat"] == 32.5
        assert persisted[1]["lng"] == -97.5
        assert persisted[2].get("lat") is None  # untouched

    @pytest.mark.asyncio
    async def test_failed_geocodes_counted_and_left_null(self, tmp_path):
        from scripts.backfill_geocode_fw_data import backfill_resources_file

        resources = [
            {"name": "X", "address": "obscure", "lat": None, "lng": None},
        ]
        path = tmp_path / "resources.json"
        path.write_text(json.dumps(resources), encoding="utf-8")

        with patch(
            "scripts.backfill_geocode_fw_data.geocode_address",
            new=AsyncMock(return_value=None),
        ):
            result = await backfill_resources_file(
                str(path), rate_limit_seconds=0,
            )

        assert result.geocoded == 0
        assert result.failed == 1
        persisted = json.loads(path.read_text(encoding="utf-8"))
        # Failed geocode must NOT fabricate coordinates.
        assert persisted[0]["lat"] is None
        assert persisted[0]["lng"] is None

    @pytest.mark.asyncio
    async def test_idempotent_on_rerun(self, tmp_path):
        """Second run with all rows already geocoded does zero API calls."""
        from scripts.backfill_geocode_fw_data import backfill_resources_file

        resources = [
            {"name": "A", "address": "1 A St", "lat": 32.0, "lng": -97.0},
            {"name": "B", "address": "2 B St", "lat": 32.5, "lng": -97.5},
        ]
        path = tmp_path / "resources.json"
        path.write_text(json.dumps(resources), encoding="utf-8")

        with patch(
            "scripts.backfill_geocode_fw_data.geocode_address",
            new=AsyncMock(return_value=(0.0, 0.0)),
        ) as mock_geo:
            result = await backfill_resources_file(
                str(path), rate_limit_seconds=0,
            )

        assert mock_geo.await_count == 0
        assert result.geocoded == 0
        assert result.skipped == 2


# ---------- Jobs DB loop -------------------------------------------


class TestJobsBackfill:
    """The jobs path goes through SQLite, not a JSON file."""

    @pytest.mark.asyncio
    async def test_jobs_backfill_updates_only_null_rows(self, tmp_path):
        from scripts.backfill_geocode_fw_data import backfill_jobs_db

        # Build a tiny SQLite mirror of the post-m010 schema.
        import sqlite3

        db_path = tmp_path / "test.db"
        con = sqlite3.connect(db_path)
        con.execute(
            "CREATE TABLE job_listings ("
            "id INTEGER PRIMARY KEY, title TEXT, company TEXT, "
            "location TEXT, description TEXT, url TEXT, source TEXT, "
            "scraped_at TEXT, expires_at TEXT, credit_check TEXT, "
            "fair_chance INTEGER, lat REAL, lng REAL)",
        )
        con.executemany(
            "INSERT INTO job_listings (title, location, scraped_at, lat, lng) "
            "VALUES (?, ?, ?, ?, ?)",
            [
                ("CNA", "Fort Worth, TX 76104", "2026-01-01", None, None),
                ("RN", "Fort Worth, TX 76110", "2026-01-01", 32.7, -97.3),
                ("Welder", "", "2026-01-01", None, None),
            ],
        )
        con.commit()
        con.close()

        with patch(
            "scripts.backfill_geocode_fw_data.geocode_address",
            new=AsyncMock(return_value=(32.74, -97.31)),
        ) as mock_geo:
            result = await backfill_jobs_db(
                str(db_path), rate_limit_seconds=0,
            )

        # Only the first row qualifies (null lat, non-empty location).
        assert mock_geo.await_count == 1
        assert result.geocoded == 1
        # Row #2 is already geocoded (skipped); row #3 has no location.
        assert result.skipped == 2
        assert result.failed == 0

        con = sqlite3.connect(db_path)
        rows = con.execute(
            "SELECT title, lat, lng FROM job_listings ORDER BY id",
        ).fetchall()
        con.close()
        assert rows[0] == ("CNA", 32.74, -97.31)
        assert rows[1] == ("RN", 32.7, -97.3)  # untouched
        assert rows[2] == ("Welder", None, None)  # untouched

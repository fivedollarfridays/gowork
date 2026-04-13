"""Tests for GET /api/city endpoint."""

import pytest


class TestCityEndpoint:
    """GET /api/city — return active city configuration."""

    @pytest.mark.anyio
    async def test_returns_city_config(self, client, test_engine):
        """Happy path: returns name, state, location, and zip_ranges."""
        resp = await client.get("/api/city")
        assert resp.status_code == 200
        data = resp.json()
        assert "name" in data
        assert "state" in data
        assert "location" in data
        assert "zip_ranges" in data
        assert isinstance(data["zip_ranges"], list)
        assert len(data["name"]) > 0

    @pytest.mark.anyio
    async def test_returns_correct_state(self, client, test_engine):
        """State is a 2-letter abbreviation."""
        resp = await client.get("/api/city")
        data = resp.json()
        assert len(data["state"]) == 2
        assert data["state"].isupper()

    @pytest.mark.anyio
    async def test_zip_ranges_not_empty(self, client, test_engine):
        """At least one ZIP range is configured."""
        resp = await client.get("/api/city")
        data = resp.json()
        assert len(data["zip_ranges"]) >= 1

    @pytest.mark.anyio
    async def test_response_has_no_extra_fields(self, client, test_engine):
        """Response should only contain the documented fields."""
        resp = await client.get("/api/city")
        data = resp.json()
        expected_keys = {"name", "state", "location", "zip_ranges"}
        assert set(data.keys()) == expected_keys

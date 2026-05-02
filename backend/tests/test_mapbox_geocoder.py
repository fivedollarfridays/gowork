"""Tests for the Mapbox forward-geocoding client.

The geocoder is intentionally minimal: in -> single address string,
out -> ``(lat, lng)`` or ``None``. Network calls go through
``async_get_with_retry`` (the same retry/backoff helper BrightData uses)
so we can assert URL shape without re-implementing httpx mocking.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import pytest


# ---------- Token resolution ----------------------------------------


class TestTokenResolution:
    """The geocoder pulls its token from MAPBOX_TOKEN, falling back to
    NEXT_PUBLIC_MAPBOX_TOKEN. Missing token -> graceful None + a single
    WARNING (caller must not have to wrap every call in try/except).
    """

    @pytest.mark.asyncio
    async def test_returns_none_when_no_token(self, monkeypatch, caplog):
        """No env var -> None, with a WARNING logged exactly once."""
        from app.integrations.mapbox import geocoder

        monkeypatch.delenv("MAPBOX_TOKEN", raising=False)
        monkeypatch.delenv("NEXT_PUBLIC_MAPBOX_TOKEN", raising=False)
        geocoder._reset_no_token_warning()

        with caplog.at_level("WARNING"):
            result = await geocoder.geocode_address(
                "1200 Circle Dr, Fort Worth, TX 76119",
            )

        assert result is None
        warning_messages = [
            r.message for r in caplog.records if r.levelname == "WARNING"
        ]
        assert any("MAPBOX_TOKEN" in m for m in warning_messages)

    @pytest.mark.asyncio
    async def test_warning_logged_only_once(self, monkeypatch, caplog):
        """Repeated no-token calls only log the warning once per process."""
        from app.integrations.mapbox import geocoder

        monkeypatch.delenv("MAPBOX_TOKEN", raising=False)
        monkeypatch.delenv("NEXT_PUBLIC_MAPBOX_TOKEN", raising=False)
        geocoder._reset_no_token_warning()

        with caplog.at_level("WARNING"):
            await geocoder.geocode_address("addr 1")
            await geocoder.geocode_address("addr 2")
            await geocoder.geocode_address("addr 3")

        warns = [r for r in caplog.records if r.levelname == "WARNING"
                 and "MAPBOX_TOKEN" in r.message]
        assert len(warns) == 1, (
            f"expected 1 warning across 3 no-token calls, got {len(warns)}"
        )

    @pytest.mark.asyncio
    async def test_falls_back_to_next_public_token(self, monkeypatch):
        """When only NEXT_PUBLIC_MAPBOX_TOKEN is set, it is used."""
        from app.integrations.mapbox import geocoder

        monkeypatch.delenv("MAPBOX_TOKEN", raising=False)
        monkeypatch.setenv("NEXT_PUBLIC_MAPBOX_TOKEN", "pk.fallback")

        captured: dict = {}

        async def fake_get(client, url, **kwargs):
            captured["url"] = url
            req = httpx.Request("GET", url)
            return httpx.Response(
                200,
                json={"features": [{"center": [-97.29, 32.71]}]},
                request=req,
            )

        with patch(
            "app.integrations.mapbox.geocoder.async_get_with_retry",
            side_effect=fake_get,
        ):
            result = await geocoder.geocode_address(
                "1200 Circle Dr Fort Worth TX",
            )

        assert result == (32.71, -97.29)
        assert "access_token=pk.fallback" in captured["url"]


# ---------- URL construction ----------------------------------------


class TestUrlShape:
    """Forward-geocoding URL must include US country bias, a DFW
    proximity hint, address-only types, and the URL-encoded address."""

    @pytest.mark.asyncio
    async def test_url_contains_required_query_params(self, monkeypatch):
        from app.integrations.mapbox import geocoder

        monkeypatch.setenv("MAPBOX_TOKEN", "pk.testtoken")

        captured: dict = {}

        async def fake_get(client, url, **kwargs):
            captured["url"] = url
            req = httpx.Request("GET", url)
            return httpx.Response(
                200,
                json={"features": [{"center": [-97.30, 32.75]}]},
                request=req,
            )

        with patch(
            "app.integrations.mapbox.geocoder.async_get_with_retry",
            side_effect=fake_get,
        ):
            await geocoder.geocode_address(
                "1200 Circle Dr, Fort Worth, TX 76119",
            )

        url = captured["url"]
        assert url.startswith(
            "https://api.mapbox.com/geocoding/v5/mapbox.places/",
        )
        assert "access_token=pk.testtoken" in url
        assert "country=US" in url
        # DFW-area proximity hint per dispatch
        assert "proximity=-97.32" in url and "32.75" in url
        assert "types=address" in url
        # Address must be URL-encoded — commas become %2C, spaces %20
        assert "%2C" in url
        assert "Circle" in url

    @pytest.mark.asyncio
    async def test_returns_lat_lng_tuple_from_first_feature(
        self, monkeypatch,
    ):
        """Mapbox returns [lng, lat] in features[0].center; we flip
        to (lat, lng) on the way out."""
        from app.integrations.mapbox import geocoder

        monkeypatch.setenv("MAPBOX_TOKEN", "pk.testtoken")

        async def fake_get(client, url, **kwargs):
            req = httpx.Request("GET", url)
            return httpx.Response(
                200,
                # Mapbox center order: [lng, lat]
                json={"features": [{"center": [-97.3208, 32.7555]}]},
                request=req,
            )

        with patch(
            "app.integrations.mapbox.geocoder.async_get_with_retry",
            side_effect=fake_get,
        ):
            result = await geocoder.geocode_address("downtown FW")

        assert result == (32.7555, -97.3208)


# ---------- Failure-mode handling ----------------------------------


class TestFailureModes:
    """Empty results, network errors, malformed payloads -> None.
    A failed geocode should never blow up the caller."""

    @pytest.mark.asyncio
    async def test_empty_features_returns_none(self, monkeypatch):
        from app.integrations.mapbox import geocoder

        monkeypatch.setenv("MAPBOX_TOKEN", "pk.testtoken")

        async def fake_get(client, url, **kwargs):
            req = httpx.Request("GET", url)
            return httpx.Response(200, json={"features": []}, request=req)

        with patch(
            "app.integrations.mapbox.geocoder.async_get_with_retry",
            side_effect=fake_get,
        ):
            result = await geocoder.geocode_address("nowhere place")

        assert result is None

    @pytest.mark.asyncio
    async def test_timeout_returns_none(self, monkeypatch):
        from app.integrations.mapbox import geocoder

        monkeypatch.setenv("MAPBOX_TOKEN", "pk.testtoken")

        async def fake_get(client, url, **kwargs):
            raise httpx.ReadTimeout("simulated timeout")

        with patch(
            "app.integrations.mapbox.geocoder.async_get_with_retry",
            side_effect=fake_get,
        ):
            result = await geocoder.geocode_address("anywhere")

        assert result is None

    @pytest.mark.asyncio
    async def test_4xx_returns_none(self, monkeypatch):
        """Non-2xx responses -> None, never a raise."""
        from app.integrations.mapbox import geocoder

        monkeypatch.setenv("MAPBOX_TOKEN", "pk.testtoken")

        async def fake_get(client, url, **kwargs):
            req = httpx.Request("GET", url)
            return httpx.Response(
                401, json={"message": "bad token"}, request=req,
            )

        with patch(
            "app.integrations.mapbox.geocoder.async_get_with_retry",
            side_effect=fake_get,
        ):
            result = await geocoder.geocode_address("anything")

        assert result is None

    @pytest.mark.asyncio
    async def test_empty_address_returns_none_without_http_call(
        self, monkeypatch,
    ):
        """Empty / whitespace address skips the API entirely."""
        from app.integrations.mapbox import geocoder

        monkeypatch.setenv("MAPBOX_TOKEN", "pk.testtoken")

        called = {"n": 0}

        async def fake_get(client, url, **kwargs):  # pragma: no cover
            called["n"] += 1
            req = httpx.Request("GET", url)
            return httpx.Response(200, json={"features": []}, request=req)

        with patch(
            "app.integrations.mapbox.geocoder.async_get_with_retry",
            side_effect=fake_get,
        ):
            assert await geocoder.geocode_address("") is None
            assert await geocoder.geocode_address("   ") is None

        assert called["n"] == 0

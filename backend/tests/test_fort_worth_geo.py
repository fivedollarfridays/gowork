"""Tests for Fort Worth geo data and geo routing."""

import pytest


class TestFortWorthGeo:
    def test_downtown_coordinates(self):
        from app.modules.matching.fort_worth_geo import DOWNTOWN_FORT_WORTH

        lat, lng = DOWNTOWN_FORT_WORTH
        assert 32.7 < lat < 32.8
        assert -97.4 < lng < -97.3

    def test_zip_centroids_have_major_zips(self):
        from app.modules.matching.fort_worth_geo import ZIP_CENTROIDS

        major_zips = ["76102", "76104", "76105", "76107", "76109", "76110", "76119"]
        for z in major_zips:
            assert z in ZIP_CENTROIDS, f"Missing ZIP {z}"

    def test_zip_centroids_coords_in_range(self):
        from app.modules.matching.fort_worth_geo import ZIP_CENTROIDS

        for z, (lat, lng) in ZIP_CENTROIDS.items():
            assert 32.5 < lat < 33.1, f"ZIP {z} lat out of range: {lat}"
            assert -97.7 < lng < -97.0, f"ZIP {z} lng out of range: {lng}"

    def test_transit_hours(self):
        from app.modules.matching.fort_worth_geo import (
            TRANSIT_START_HOUR,
            TRANSIT_END_HOUR,
        )

        assert TRANSIT_START_HOUR == 5
        assert TRANSIT_END_HOUR >= 22  # Trinity Metro runs later


class TestGeoRouter:
    def test_montgomery_returns_montgomery_data(self):
        from unittest.mock import patch
        from app.modules.matching.geo_router import get_downtown_coords, get_zip_centroids
        from app.cities.config import CityConfig

        cfg = CityConfig(
            name="Montgomery", state="AL", location="Montgomery, AL",
            zip_ranges=["36101-36120"], job_adapters=["brightdata"],
            data_dir="data/cities/montgomery",
        )
        with patch("app.modules.matching.geo_router.get_city_config", return_value=cfg):
            coords = get_downtown_coords()
            assert abs(coords[0] - 32.3668) < 0.01  # Montgomery lat

    def test_fort_worth_returns_fort_worth_data(self):
        from unittest.mock import patch
        from app.modules.matching.geo_router import get_downtown_coords, get_zip_centroids
        from app.cities.config import CityConfig

        cfg = CityConfig(
            name="Fort Worth", state="TX", location="Fort Worth, TX",
            zip_ranges=["76101-76199"], job_adapters=["twc"],
            data_dir="data/cities/fort-worth",
        )
        with patch("app.modules.matching.geo_router.get_city_config", return_value=cfg):
            coords = get_downtown_coords()
            assert abs(coords[0] - 32.7555) < 0.01  # Fort Worth lat

    def test_zip_centroids_routed_correctly(self):
        from unittest.mock import patch
        from app.modules.matching.geo_router import get_zip_centroids
        from app.cities.config import CityConfig

        cfg = CityConfig(
            name="Fort Worth", state="TX", location="Fort Worth, TX",
            zip_ranges=["76101-76199"], job_adapters=["twc"],
            data_dir="data/cities/fort-worth",
        )
        with patch("app.modules.matching.geo_router.get_city_config", return_value=cfg):
            centroids = get_zip_centroids()
            assert "76102" in centroids
            assert "36104" not in centroids

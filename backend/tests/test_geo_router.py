"""Tests for geo data routing by city config."""

from unittest.mock import patch

from app.cities.config import CityConfig


def _mock_city_config(state: str) -> CityConfig:
    city_map = {
        "AL": CityConfig(
            name="Montgomery", state="AL", location="Montgomery, AL",
            zip_ranges=["36101-36120"], job_adapters=["brightdata"],
            data_dir="data/cities/montgomery",
        ),
        "TX": CityConfig(
            name="Fort Worth", state="TX", location="Fort Worth, TX",
            zip_ranges=["76101-76199"], job_adapters=["twc", "usajobs"],
            data_dir="data/cities/fort-worth",
        ),
    }
    return city_map[state]


_PATCH_TARGET = "app.modules.matching.geo_router.get_city_config"


class TestGetDowntownCoords:
    def test_returns_montgomery_for_al(self):
        from app.modules.matching.geo_router import get_downtown_coords

        with patch(_PATCH_TARGET, return_value=_mock_city_config("AL")):
            coords = get_downtown_coords()
            assert abs(coords[0] - 32.3668) < 0.01

    def test_returns_fort_worth_for_tx(self):
        from app.modules.matching.geo_router import get_downtown_coords

        with patch(_PATCH_TARGET, return_value=_mock_city_config("TX")):
            coords = get_downtown_coords()
            assert abs(coords[0] - 32.7555) < 0.01


class TestGetZipCentroids:
    def test_returns_montgomery_zips_for_al(self):
        from app.modules.matching.geo_router import get_zip_centroids

        with patch(_PATCH_TARGET, return_value=_mock_city_config("AL")):
            centroids = get_zip_centroids()
            assert isinstance(centroids, dict)
            assert any(k.startswith("361") for k in centroids)

    def test_returns_fort_worth_zips_for_tx(self):
        from app.modules.matching.geo_router import get_zip_centroids

        with patch(_PATCH_TARGET, return_value=_mock_city_config("TX")):
            centroids = get_zip_centroids()
            assert isinstance(centroids, dict)
            assert any(k.startswith("761") for k in centroids)


class TestGetTransitHours:
    def test_returns_tuple_for_al(self):
        from app.modules.matching.geo_router import get_transit_hours

        with patch(_PATCH_TARGET, return_value=_mock_city_config("AL")):
            start, end = get_transit_hours()
            assert start == 5
            assert end == 21

    def test_returns_tuple_for_tx(self):
        from app.modules.matching.geo_router import get_transit_hours

        with patch(_PATCH_TARGET, return_value=_mock_city_config("TX")):
            start, end = get_transit_hours()
            assert start == 5
            assert end == 22

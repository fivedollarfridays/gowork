"""Coverage push tests for geo_router and resource_router TX paths.

Targets uncovered lines:
- geo_router.py lines 28-36 (get_transit_hours TX path)
- resource_router.py lines 32-33, 42-43, 52-53 (TX paths for career_center_step,
  resource_affinity, cert_db)
"""

import pytest
from unittest.mock import patch
from app.cities.config import CityConfig


def _mock_tx():
    return CityConfig(
        name="Fort Worth", state="TX", location="Fort Worth, TX",
        zip_ranges=["76101-76199"], job_adapters=["twc"],
        data_dir="data/cities/fort-worth",
    )


def _mock_al():
    return CityConfig(
        name="Montgomery", state="AL", location="Montgomery, AL",
        zip_ranges=["36101-36120"], job_adapters=["brightdata"],
        data_dir="data/cities/montgomery",
    )


class TestGeoRouterTransitHours:
    """Cover geo_router.get_transit_hours for both cities."""

    def test_fort_worth_transit_hours(self):
        from app.modules.matching.geo_router import get_transit_hours

        with patch("app.modules.matching.geo_router.get_city_config", return_value=_mock_tx()):
            start, end = get_transit_hours()
            # Trinity Metro: 5am - 10pm
            assert start == 5
            assert end == 22

    def test_montgomery_transit_hours(self):
        from app.modules.matching.geo_router import get_transit_hours

        with patch("app.modules.matching.geo_router.get_city_config", return_value=_mock_al()):
            start, end = get_transit_hours()
            # M-Transit schedule
            assert isinstance(start, int)
            assert isinstance(end, int)
            assert start < end

    def test_fort_worth_zip_centroids(self):
        from app.modules.matching.geo_router import get_zip_centroids

        with patch("app.modules.matching.geo_router.get_city_config", return_value=_mock_tx()):
            centroids = get_zip_centroids()
            assert "76102" in centroids
            assert "36104" not in centroids

    def test_montgomery_zip_centroids(self):
        from app.modules.matching.geo_router import get_zip_centroids

        with patch("app.modules.matching.geo_router.get_city_config", return_value=_mock_al()):
            centroids = get_zip_centroids()
            assert "36104" in centroids
            assert "76102" not in centroids


class TestResourceRouterTxPaths:
    """Cover resource_router TX paths for career_center_step, resource_affinity, cert_db."""

    def test_fort_worth_career_center_step(self):
        from app.modules.matching.resource_router import get_career_center_step

        with patch("app.modules.matching.resource_router.get_city_config", return_value=_mock_tx()):
            step = get_career_center_step()
            assert "Workforce Solutions" in step
            assert "817" in step  # Fort Worth area code

    def test_montgomery_career_center_step(self):
        from app.modules.matching.resource_router import get_career_center_step

        with patch("app.modules.matching.resource_router.get_city_config", return_value=_mock_al()):
            step = get_career_center_step()
            assert "Alabama" in step or "Career Center" in step

    def test_fort_worth_resource_affinity(self):
        from app.modules.matching.resource_router import get_resource_affinity

        with patch("app.modules.matching.resource_router.get_city_config", return_value=_mock_tx()):
            affinity = get_resource_affinity()
            # Fort Worth resources should include Trinity Metro
            assert "trinity metro" in affinity
            assert "workforce solutions" in affinity

    def test_montgomery_resource_affinity(self):
        from app.modules.matching.resource_router import get_resource_affinity

        with patch("app.modules.matching.resource_router.get_city_config", return_value=_mock_al()):
            affinity = get_resource_affinity()
            # Montgomery resources should not have Trinity Metro
            assert "trinity metro" not in affinity

    def test_fort_worth_cert_db(self):
        from app.modules.matching.resource_router import get_cert_db

        with patch("app.modules.matching.resource_router.get_city_config", return_value=_mock_tx()):
            db = get_cert_db()
            assert "CNA" in db
            assert "Texas" in db["CNA"]["renewal_body"]["name"]

    def test_montgomery_cert_db(self):
        from app.modules.matching.resource_router import get_cert_db

        with patch("app.modules.matching.resource_router.get_city_config", return_value=_mock_al()):
            db = get_cert_db()
            assert "CNA" in db
            assert "Alabama" in db["CNA"]["renewal_body"]["name"]


class TestResourceRouterBarrierActions:
    """Ensure barrier actions return correct city-specific data."""

    def test_fort_worth_barrier_actions_all_types(self):
        from app.modules.matching.resource_router import get_barrier_actions
        from app.modules.matching.types import BarrierType

        with patch("app.modules.matching.resource_router.get_city_config", return_value=_mock_tx()):
            actions = get_barrier_actions()
            # All 7 barrier types should have actions
            for bt in BarrierType:
                assert bt in actions, f"Missing actions for {bt}"
                assert len(actions[bt]) > 0

    def test_montgomery_barrier_actions_all_types(self):
        from app.modules.matching.resource_router import get_barrier_actions
        from app.modules.matching.types import BarrierType

        with patch("app.modules.matching.resource_router.get_city_config", return_value=_mock_al()):
            actions = get_barrier_actions()
            for bt in BarrierType:
                assert bt in actions, f"Missing actions for {bt}"
                assert len(actions[bt]) > 0

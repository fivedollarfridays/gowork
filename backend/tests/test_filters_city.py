"""Tests verifying filters.py is city-aware for childcare and transit."""

from unittest.mock import patch

from app.cities.config import CityConfig
from app.modules.matching.filters import apply_childcare_filter, apply_transit_filter
from app.modules.matching.types import JobMatch, Resource


def _fw_config():
    return CityConfig(
        name="Fort Worth", state="TX", location="Fort Worth, TX",
        zip_ranges=["76101-76199"], job_adapters=["twc"],
        data_dir="data/cities/fort-worth",
    )


def _make_job(**overrides) -> JobMatch:
    defaults = {"title": "Clerk", "company": "ACME"}
    defaults.update(overrides)
    return JobMatch(**defaults)


def _make_resource(**overrides) -> Resource:
    defaults = {"id": 1, "name": "Provider A", "category": "childcare"}
    defaults.update(overrides)
    return Resource(**defaults)


class TestChildcareFilterCityAware:
    """Verify childcare filter uses city-aware ZIP ranges."""

    def test_fort_worth_zip_included(self):
        """Fort Worth childcare resources (761xx) should be included for FW users."""
        with patch("app.modules.matching.filters.get_city_config", return_value=_fw_config()):
            resources = [
                _make_resource(id=1, name="FW Childcare", address="123 Main St, Fort Worth, TX 76102"),
                _make_resource(id=2, name="AL Childcare", address="456 Oak St, Montgomery, AL 36104"),
            ]
            result = apply_childcare_filter(resources, "76101", ["76102"])
            names = [r.name for r in result]
            assert "FW Childcare" in names

    def test_montgomery_zip_excluded_for_fort_worth(self):
        """Montgomery 361xx resources should NOT match for Fort Worth users."""
        with patch("app.modules.matching.filters.get_city_config", return_value=_fw_config()):
            resources = [
                _make_resource(id=1, name="AL Only", address="100 Oak Ave, Montgomery, AL 36117"),
            ]
            result = apply_childcare_filter(resources, "76101", [])
            # Should NOT include Montgomery resource for Fort Worth
            assert len(result) == 0


class TestTransitFilterNoMTransit:
    """Verify transit filter does not default to 'M-Transit'."""

    def test_default_route_name_not_m_transit(self):
        """When route has no route_name, default should not be 'M-Transit'."""
        jobs = [_make_job(title="Clerk", location="Downtown")]
        routes = [{"route_number": 3}]  # No route_name key
        result = apply_transit_filter(jobs, routes, "36101")
        assert result[0].route != "M-Transit"

    def test_explicit_route_name_preserved(self):
        """When route has explicit name, it should be used as-is."""
        jobs = [_make_job(title="Clerk", location="Downtown")]
        routes = [{"route_number": 3, "route_name": "Trinity Metro Route 2"}]
        result = apply_transit_filter(jobs, routes, "76101")
        assert result[0].route == "Trinity Metro Route 2"

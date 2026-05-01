"""Tests for the keyword-based transit fallback in job_matcher.

When a job listing has no lat/lng we can't run the real transit-stop
proximity check, so the matcher falls back to a keyword scan over the
title/description/location.  That keyword has to match the active
city — pre-purge it was hardcoded to ``montgomery``, which made every
Fort Worth listing without coords look transit-inaccessible.

These tests pin the behavior to ``get_city_config().name.lower()`` so a
future city onboarding doesn't regress it.
"""

from unittest.mock import patch

from app.cities.config import CityConfig
from app.modules.matching.job_matcher import _keyword_transit_check


def _fw_config() -> CityConfig:
    return CityConfig(
        name="Fort Worth", state="TX", location="Fort Worth, TX",
        zip_ranges=["76101-76199"], job_adapters=["honestjobs"],
        data_dir="data/cities/fort-worth",
    )


def _mont_config() -> CityConfig:
    return CityConfig(
        name="Montgomery", state="AL", location="Montgomery, AL",
        zip_ranges=["36101-36120"], job_adapters=["honestjobs"],
        data_dir="data/cities/montgomery",
    )


class TestKeywordTransitCheck:
    def test_fort_worth_active_matches_fort_worth_listings(self):
        job = {"title": "Custodian", "location": "Fort Worth, TX",
               "description": "near downtown"}
        with patch(
            "app.modules.matching.job_matcher.get_city_config",
            return_value=_fw_config(),
        ):
            accessible, _ = _keyword_transit_check(job)
        assert accessible is True

    def test_fort_worth_active_misses_montgomery_listings(self):
        job = {"title": "Cook", "location": "Montgomery, AL",
               "description": "diner work"}
        with patch(
            "app.modules.matching.job_matcher.get_city_config",
            return_value=_fw_config(),
        ):
            accessible, _ = _keyword_transit_check(job)
        assert accessible is False

    def test_montgomery_active_matches_montgomery_listings(self):
        job = {"title": "Cashier", "location": "Montgomery, AL",
               "description": "midtown shift"}
        with patch(
            "app.modules.matching.job_matcher.get_city_config",
            return_value=_mont_config(),
        ):
            accessible, _ = _keyword_transit_check(job)
        assert accessible is True

    def test_returns_sunday_flag_independently_of_city(self):
        job = {"title": "Driver", "location": "Fort Worth, TX",
               "description": "Sunday shift required"}
        with patch(
            "app.modules.matching.job_matcher.get_city_config",
            return_value=_fw_config(),
        ):
            accessible, sunday = _keyword_transit_check(job)
        assert accessible is True
        assert sunday is True

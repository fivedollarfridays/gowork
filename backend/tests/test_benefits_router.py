"""Tests for benefits module routing by city config."""

import pytest
from unittest.mock import patch


def _mock_city_config(state: str):
    """Create a mock CityConfig with the given state."""
    from app.cities.config import CityConfig

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


class TestGetProgramChecks:
    def test_returns_alabama_checks_for_al(self):
        from app.modules.benefits.router import get_program_checks

        with patch("app.modules.benefits.router.get_city_config", return_value=_mock_city_config("AL")):
            checks = get_program_checks()
            assert "ALL_Kids" in checks
            assert "CHIP" not in checks

    def test_returns_texas_checks_for_tx(self):
        from app.modules.benefits.router import get_program_checks

        with patch("app.modules.benefits.router.get_city_config", return_value=_mock_city_config("TX")):
            checks = get_program_checks()
            assert "CHIP" in checks
            assert "ALL_Kids" not in checks

    def test_returns_ceap_for_texas(self):
        from app.modules.benefits.router import get_program_checks

        with patch("app.modules.benefits.router.get_city_config", return_value=_mock_city_config("TX")):
            checks = get_program_checks()
            assert "CEAP" in checks
            assert "LIHEAP" not in checks


class TestGetApplicationData:
    def test_alabama_data_has_dhr(self):
        from app.modules.benefits.router import get_application_data

        with patch("app.modules.benefits.router.get_city_config", return_value=_mock_city_config("AL")):
            data = get_application_data()
            assert "SNAP" in data
            assert "DHR" in data["SNAP"].office_name

    def test_texas_data_has_hhsc(self):
        from app.modules.benefits.router import get_application_data

        with patch("app.modules.benefits.router.get_city_config", return_value=_mock_city_config("TX")):
            data = get_application_data()
            assert "SNAP" in data
            assert "HHSC" in data["SNAP"].office_name or "Tarrant" in data["SNAP"].office_name


class TestGetValidPrograms:
    def test_alabama_has_all_kids(self):
        from app.modules.benefits.router import get_valid_programs

        with patch("app.modules.benefits.router.get_city_config", return_value=_mock_city_config("AL")):
            programs = get_valid_programs()
            assert "ALL_Kids" in programs
            assert "CHIP" not in programs

    def test_texas_has_chip(self):
        from app.modules.benefits.router import get_valid_programs

        with patch("app.modules.benefits.router.get_city_config", return_value=_mock_city_config("TX")):
            programs = get_valid_programs()
            assert "CHIP" in programs
            assert "ALL_Kids" not in programs


class TestGetScreenerDisclaimer:
    def test_alabama_mentions_dhr(self):
        from app.modules.benefits.router import get_screener_disclaimer

        with patch("app.modules.benefits.router.get_city_config", return_value=_mock_city_config("AL")):
            disclaimer = get_screener_disclaimer()
            assert "Alabama" in disclaimer or "DHR" in disclaimer

    def test_texas_mentions_hhsc(self):
        from app.modules.benefits.router import get_screener_disclaimer

        with patch("app.modules.benefits.router.get_city_config", return_value=_mock_city_config("TX")):
            disclaimer = get_screener_disclaimer()
            assert "Texas" in disclaimer or "HHSC" in disclaimer

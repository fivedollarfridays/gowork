"""Tests for city-aware ZIP code validation."""

import pytest
from unittest.mock import patch
from app.cities.config import CityConfig


def _al_config():
    return CityConfig(
        name="Montgomery", state="AL", location="Montgomery, AL",
        zip_ranges=["36101-36120", "36130", "36140-36142"],
        job_adapters=["brightdata"], data_dir="data/cities/montgomery",
    )


def _tx_config():
    return CityConfig(
        name="Fort Worth", state="TX", location="Fort Worth, TX",
        zip_ranges=["76101-76199"],
        job_adapters=["twc"], data_dir="data/cities/fort-worth",
    )


class TestZipRangeParser:
    def test_single_zip(self):
        from app.modules.matching.zip_validation import parse_zip_ranges

        result = parse_zip_ranges(["36130"])
        assert "36130" in result

    def test_zip_range(self):
        from app.modules.matching.zip_validation import parse_zip_ranges

        result = parse_zip_ranges(["36101-36105"])
        assert "36101" in result
        assert "36103" in result
        assert "36105" in result
        assert "36106" not in result

    def test_multiple_ranges(self):
        from app.modules.matching.zip_validation import parse_zip_ranges

        result = parse_zip_ranges(["36101-36103", "36130"])
        assert len(result) == 4  # 36101, 36102, 36103, 36130


class TestCityAwareValidation:
    def test_montgomery_accepts_361xx(self):
        from app.modules.matching.zip_validation import is_valid_zip_for_city

        assert is_valid_zip_for_city("36104", _al_config())

    def test_montgomery_rejects_761xx(self):
        from app.modules.matching.zip_validation import is_valid_zip_for_city

        assert not is_valid_zip_for_city("76102", _al_config())

    def test_fort_worth_accepts_761xx(self):
        from app.modules.matching.zip_validation import is_valid_zip_for_city

        assert is_valid_zip_for_city("76102", _tx_config())
        assert is_valid_zip_for_city("76199", _tx_config())

    def test_fort_worth_rejects_361xx(self):
        from app.modules.matching.zip_validation import is_valid_zip_for_city

        assert not is_valid_zip_for_city("36104", _tx_config())

    def test_rejects_non_5digit(self):
        from app.modules.matching.zip_validation import is_valid_zip_for_city

        assert not is_valid_zip_for_city("1234", _al_config())
        assert not is_valid_zip_for_city("123456", _al_config())
        assert not is_valid_zip_for_city("abcde", _al_config())


class TestZipRegexForCity:
    def test_montgomery_regex(self):
        from app.modules.matching.zip_validation import get_zip_regex_for_city
        import re

        pattern = get_zip_regex_for_city(_al_config())
        assert re.match(pattern, "36104")
        assert not re.match(pattern, "76102")

    def test_fort_worth_regex(self):
        from app.modules.matching.zip_validation import get_zip_regex_for_city
        import re

        pattern = get_zip_regex_for_city(_tx_config())
        assert re.match(pattern, "76102")
        assert not re.match(pattern, "36104")

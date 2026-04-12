"""Edge-case tests for ZIP code validation.

Targets uncovered lines:
- zip_validation.py line 50 (empty valid_zips)
- zip_validation.py line 68 (short common prefix in regex)
Plus comprehensive edge cases for boundary ZIPs.
"""

import re

import pytest
from app.cities.config import CityConfig
from app.modules.matching.zip_validation import (
    get_zip_regex_for_city,
    is_valid_zip_for_city,
    parse_zip_ranges,
)


def _tx_config():
    return CityConfig(
        name="Fort Worth", state="TX", location="Fort Worth, TX",
        zip_ranges=["76101-76199"],
        job_adapters=["twc"], data_dir="data/cities/fort-worth",
    )


def _al_config():
    return CityConfig(
        name="Montgomery", state="AL", location="Montgomery, AL",
        zip_ranges=["36101-36120", "36130", "36140-36142"],
        job_adapters=["brightdata"], data_dir="data/cities/montgomery",
    )


class TestZipEdgeCases:
    """Input edge cases for ZIP validation."""

    def test_empty_string(self):
        assert not is_valid_zip_for_city("", _tx_config())

    def test_four_digit(self):
        assert not is_valid_zip_for_city("7610", _tx_config())

    def test_six_digit(self):
        assert not is_valid_zip_for_city("761020", _tx_config())

    def test_alphabetic(self):
        assert not is_valid_zip_for_city("abcde", _tx_config())

    def test_special_chars(self):
        assert not is_valid_zip_for_city("76-02", _tx_config())

    def test_whitespace(self):
        assert not is_valid_zip_for_city(" 76102", _tx_config())

    def test_none_like_string(self):
        assert not is_valid_zip_for_city("None", _tx_config())


class TestZipBoundaries:
    """ZIP codes at exact range boundaries."""

    def test_fort_worth_just_below_range(self):
        """ZIP 76100 is just below the Fort Worth range (76101-76199)."""
        assert not is_valid_zip_for_city("76100", _tx_config())

    def test_fort_worth_start_of_range(self):
        """ZIP 76101 is the start of the range."""
        assert is_valid_zip_for_city("76101", _tx_config())

    def test_fort_worth_end_of_range(self):
        """ZIP 76199 is the end of the range."""
        assert is_valid_zip_for_city("76199", _tx_config())

    def test_fort_worth_just_above_range(self):
        """ZIP 76200 is just above the Fort Worth range."""
        assert not is_valid_zip_for_city("76200", _tx_config())

    def test_montgomery_just_below_range(self):
        """ZIP 36100 is just below Montgomery's first range."""
        assert not is_valid_zip_for_city("36100", _al_config())

    def test_montgomery_end_of_first_range(self):
        """ZIP 36120 should be accepted (end of first range)."""
        assert is_valid_zip_for_city("36120", _al_config())

    def test_montgomery_gap_zip(self):
        """ZIP 36125 is in the gap between ranges."""
        assert not is_valid_zip_for_city("36125", _al_config())

    def test_montgomery_single_zip(self):
        """ZIP 36130 is a standalone entry."""
        assert is_valid_zip_for_city("36130", _al_config())


class TestZipRegexEdgeCases:
    """Edge cases for regex generation from ZIP ranges."""

    def test_empty_ranges_fallback(self):
        """Empty zip_ranges should produce a generic 5-digit regex."""
        config = CityConfig(
            name="Empty", state="XX", location="Nowhere",
            zip_ranges=[], job_adapters=[], data_dir="data/cities/empty",
        )
        pattern = get_zip_regex_for_city(config)
        assert pattern == r"^\d{5}$"

    def test_short_prefix_fallback(self):
        """Ranges with short common prefix (< 3 chars) should fallback."""
        config = CityConfig(
            name="Wide", state="XX", location="Everywhere",
            zip_ranges=["10001-10005", "90001-90005"],
            job_adapters=[], data_dir="data/cities/wide",
        )
        pattern = get_zip_regex_for_city(config)
        # Common prefix of 10001 and 90005 is empty -> fallback
        assert pattern == r"^\d{5}$"

    def test_three_char_prefix_produces_pattern(self):
        """Ranges with 3-char prefix should produce a specific regex."""
        config = CityConfig(
            name="Test", state="XX", location="Test",
            zip_ranges=["76101-76199"],
            job_adapters=[], data_dir="data/cities/test",
        )
        pattern = get_zip_regex_for_city(config)
        assert re.match(pattern, "76150")
        assert not re.match(pattern, "77150")

    def test_single_zip_produces_exact_prefix(self):
        """A single ZIP should produce a very specific regex."""
        config = CityConfig(
            name="Single", state="XX", location="Single",
            zip_ranges=["36130"],
            job_adapters=[], data_dir="data/cities/single",
        )
        pattern = get_zip_regex_for_city(config)
        assert re.match(pattern, "36130")


class TestParseZipRanges:
    """parse_zip_ranges edge cases."""

    def test_empty_list(self):
        result = parse_zip_ranges([])
        assert result == set()

    def test_single_entry(self):
        result = parse_zip_ranges(["99999"])
        assert result == {"99999"}

    def test_range_single_element(self):
        """Range where start == end should produce one element."""
        result = parse_zip_ranges(["36130-36130"])
        assert result == {"36130"}

    def test_large_range(self):
        """76101-76199 should produce 99 ZIPs."""
        result = parse_zip_ranges(["76101-76199"])
        assert len(result) == 99
        assert "76101" in result
        assert "76199" in result

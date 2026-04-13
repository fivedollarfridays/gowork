"""Edge case tests for fair_chance_index -- invalid slugs, malformed data, I/O errors.

Covers uncovered lines 25-26, 35, 37-39 in fair_chance_index.py:
- Invalid city slug pattern rejection
- Non-list JSON data handling
- JSON decode error handling
"""

import json
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from app.modules.criminal.fair_chance_index import (
    get_fair_chance_employers,
    load_employers,
)


class TestLoadEmployersInvalidSlug:
    """Invalid city slug pattern rejection (line 25-26)."""

    def test_slug_with_uppercase_rejected(self):
        """Uppercase chars don't match [a-z][a-z0-9-] pattern."""
        load_employers.cache_clear()
        result = load_employers("Fort-Worth")
        assert result == ()

    def test_slug_starting_with_number_rejected(self):
        """Slug starting with a digit is invalid."""
        load_employers.cache_clear()
        result = load_employers("1city")
        assert result == ()

    def test_slug_with_special_chars_rejected(self):
        """Slug with special characters is invalid."""
        load_employers.cache_clear()
        result = load_employers("city@name!")
        assert result == ()

    def test_empty_slug_rejected(self):
        """Empty string doesn't match pattern."""
        load_employers.cache_clear()
        result = load_employers("")
        assert result == ()

    def test_slug_too_long_rejected(self):
        """Slug over 50 chars is rejected by pattern."""
        load_employers.cache_clear()
        result = load_employers("a" * 51)
        assert result == ()


class TestLoadEmployersMalformedData:
    """Non-list JSON and decode errors (lines 35, 37-39)."""

    def test_json_file_with_dict_returns_empty(self):
        """JSON file containing a dict (not list) returns empty tuple."""
        load_employers.cache_clear()
        mock_data = json.dumps({"employer": "test"})
        with patch("builtins.open", mock_open(read_data=mock_data)):
            with patch.object(Path, "exists", return_value=True):
                result = load_employers("test-city")
        assert result == ()

    def test_json_file_with_string_returns_empty(self):
        """JSON file containing a string (not list) returns empty tuple."""
        load_employers.cache_clear()
        mock_data = json.dumps("just a string")
        with patch("builtins.open", mock_open(read_data=mock_data)):
            with patch.object(Path, "exists", return_value=True):
                result = load_employers("test-city-str")
        assert result == ()

    def test_invalid_json_returns_empty(self):
        """Corrupt JSON file returns empty tuple (JSONDecodeError path)."""
        load_employers.cache_clear()
        with patch("builtins.open", mock_open(read_data="{not valid json")):
            with patch.object(Path, "exists", return_value=True):
                result = load_employers("corrupt-city")
        assert result == ()

    def test_os_error_returns_empty(self):
        """OSError during file read returns empty tuple."""
        load_employers.cache_clear()
        with patch("builtins.open", side_effect=OSError("Permission denied")):
            with patch.object(Path, "exists", return_value=True):
                result = load_employers("unreadable-city")
        assert result == ()


class TestGetFairChanceEmployersEdgeCases:
    """Edge cases for get_fair_chance_employers."""

    def test_non_dict_entries_filtered(self):
        """Non-dict entries in employer list are filtered out."""
        load_employers.cache_clear()
        mock_data = json.dumps([
            {"name": "Good Corp", "fair_chance": True},
            "not a dict",
            42,
            {"name": "Bad Corp", "fair_chance": False},
        ])
        with patch("builtins.open", mock_open(read_data=mock_data)):
            with patch.object(Path, "exists", return_value=True):
                result = get_fair_chance_employers("mixed-city")
        assert len(result) == 1
        assert result[0]["name"] == "Good Corp"

    def test_fair_chance_must_be_true_not_truthy(self):
        """fair_chance must be exactly True, not just truthy."""
        load_employers.cache_clear()
        mock_data = json.dumps([
            {"name": "Corp A", "fair_chance": True},
            {"name": "Corp B", "fair_chance": 1},
            {"name": "Corp C", "fair_chance": "yes"},
        ])
        with patch("builtins.open", mock_open(read_data=mock_data)):
            with patch.object(Path, "exists", return_value=True):
                result = get_fair_chance_employers("strict-city")
        assert len(result) == 1
        assert result[0]["name"] == "Corp A"

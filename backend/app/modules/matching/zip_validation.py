"""City-aware ZIP code validation.

Parses zip_ranges from CityConfig and validates ZIP codes dynamically
based on the active city, replacing the hardcoded ^361\\d{2}$ regex.
"""

from __future__ import annotations

import re
from functools import lru_cache
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.cities.config import CityConfig

_ZIP_RE = re.compile(r"^\d{5}$")


def parse_zip_ranges(ranges: list[str]) -> set[str]:
    """Parse zip_ranges from CityConfig into a set of valid ZIP strings.

    Supports formats: "36130" (single) and "36101-36120" (inclusive range).
    """
    valid: set[str] = set()
    for entry in ranges:
        if "-" in entry:
            start, end = entry.split("-", 1)
            for z in range(int(start), int(end) + 1):
                valid.add(f"{z:05d}")
        else:
            valid.add(entry)
    return valid


@lru_cache(maxsize=8)
def _cached_zip_set(ranges_key: tuple[str, ...]) -> frozenset[str]:
    return frozenset(parse_zip_ranges(list(ranges_key)))


def is_valid_zip_for_city(zip_code: str, city_config: CityConfig) -> bool:
    """Check if a ZIP code is valid for the given city config."""
    if not _ZIP_RE.match(zip_code):
        return False
    valid_zips = _cached_zip_set(tuple(city_config.zip_ranges))
    return zip_code in valid_zips


def get_zip_regex_for_city(city_config: CityConfig) -> str:
    """Generate a regex pattern that matches valid ZIPs for a city.

    Uses the common prefix of the zip_ranges to build a simple pattern.
    For example, ["76101-76199"] -> "^761\\d{2}$"
    """
    valid_zips = parse_zip_ranges(city_config.zip_ranges)
    if not valid_zips:
        return r"^\d{5}$"

    # Find common prefix
    sorted_zips = sorted(valid_zips)
    first = sorted_zips[0]
    last = sorted_zips[-1]
    prefix_len = 0
    for i in range(min(len(first), len(last))):
        if first[i] == last[i]:
            prefix_len += 1
        else:
            break

    if prefix_len >= 3:
        prefix = first[:prefix_len]
        remaining = 5 - prefix_len
        return f"^{re.escape(prefix)}\\d{{{remaining}}}$"

    return r"^\d{5}$"

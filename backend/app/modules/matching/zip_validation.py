"""City-aware ZIP code validation.

Parses zip_ranges from CityConfig and validates ZIP codes dynamically.
Supports both single-city validation and agnostic mode that accepts
ZIPs from ANY configured city.
"""

from __future__ import annotations

import re
from functools import lru_cache
from typing import TYPE_CHECKING, Optional

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


# ── Agnostic helpers (accept ZIPs from any configured city) ────────


@lru_cache(maxsize=1)
def _all_city_zip_maps() -> dict[str, frozenset[str]]:
    """Load all city configs and build slug → valid-ZIPs mapping.

    Scanned once and cached for the lifetime of the process.
    """
    from app.cities.config import CITIES_DIR, load_city_config

    result: dict[str, frozenset[str]] = {}
    cities_dir = CITIES_DIR.resolve()
    if not cities_dir.exists():
        return result
    for yaml_path in sorted(cities_dir.glob("*.yaml")):
        slug = yaml_path.stem
        try:
            cfg = load_city_config(slug)
            result[slug] = frozenset(parse_zip_ranges(cfg.zip_ranges))
        except Exception:
            continue
    return result


def resolve_city_for_zip(zip_code: str) -> Optional[str]:
    """Return the city slug whose zip_ranges contain *zip_code*, or None."""
    if not _ZIP_RE.match(zip_code):
        return None
    for slug, zips in _all_city_zip_maps().items():
        if zip_code in zips:
            return slug
    return None


def is_valid_zip_for_any_city(zip_code: str) -> bool:
    """Return True if *zip_code* belongs to ANY configured city."""
    return resolve_city_for_zip(zip_code) is not None

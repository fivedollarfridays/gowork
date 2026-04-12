"""Fair-chance employer index -- city-aware employer loading and filtering."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

_logger = logging.getLogger(__name__)

_DATA_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent / "data" / "cities"
_CITY_SLUG_RE = re.compile(r"^[a-z][a-z0-9-]{0,49}$")


def load_employers(city_slug: str) -> list[dict]:
    """Load employer data from the city's data directory.

    Returns empty list if file is missing or malformed.
    """
    if not _CITY_SLUG_RE.match(city_slug):
        _logger.warning("Invalid city slug: %s", city_slug)
        return []
    path = _DATA_ROOT / city_slug / "employers.json"
    if not path.exists():
        _logger.warning("No employer data for city: %s", city_slug)
        return []
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            return []
        return data
    except (json.JSONDecodeError, OSError):
        _logger.warning("Failed to load employer data for %s", city_slug)
        return []


def get_fair_chance_employers(city_slug: str) -> list[dict]:
    """Return only fair-chance employers for a city."""
    return [e for e in load_employers(city_slug) if e.get("fair_chance") is True]

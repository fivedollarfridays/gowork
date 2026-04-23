"""City-aware work-date helpers (T12.3).

Ported from `ops:lib/nightly_day_boundary.py` and made city-generic. The work
date is the "day that just ended" for a given city: a nightly job running at
02:30 local time should attribute its work to yesterday's calendar date, not
today's. The rollover hour defaults to 4 (so 02:00 nightly cron, which is
before 04:00, is still "yesterday"); cities may override via their config.

The timezone registry is sourced from `app.modules.common.temporal_types`
(`TIMEZONE_BY_CITY`) so we never build a parallel map. Unknown cities raise
`KeyError`.

Callers:
    from app.core.day_boundary import current_work_date, resolve_work_date
    work_date = current_work_date("montgomery")
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

from app.modules.common.temporal_types import TIMEZONE_BY_CITY

DEFAULT_ROLLOVER_HOUR = 4

# Per-city rollover cache — lazily populated, cleared in tests via
# `_rollover_cache_clear()`.
_ROLLOVER_CACHE: dict[str, int] = {}


def _rollover_cache_clear() -> None:
    """Reset the cached rollover-hour map (test-only helper)."""
    _ROLLOVER_CACHE.clear()


def _tz_for_city(city: str) -> ZoneInfo:
    """Look up the IANA zone for `city`; raise KeyError if unknown."""
    tz_name = TIMEZONE_BY_CITY.get(city)
    if tz_name is None:
        raise KeyError(f"No timezone configured for city {city!r}")
    return ZoneInfo(tz_name)


def _load_city_config_for_rollover(city: str) -> Any:
    """Load the city config object used for rollover resolution.

    Broken out so tests can monkeypatch without touching the real YAML
    loader. Returns the CityConfig or None if loading fails.
    """
    try:
        from app.cities.config import load_city_config

        return load_city_config(city)
    except Exception:  # pragma: no cover — defensive: missing YAML
        return None


def _resolve_rollover_hour(city: str) -> int:
    """Return the rollover hour for `city` (default 4).

    Checks the city config for a `rollover_hour` attribute; falls back to
    `DEFAULT_ROLLOVER_HOUR` otherwise. Results cached per city.
    """
    cached = _ROLLOVER_CACHE.get(city)
    if cached is not None:
        return cached

    cfg = _load_city_config_for_rollover(city)
    hour = getattr(cfg, "rollover_hour", None) if cfg is not None else None
    if not isinstance(hour, int):
        hour = DEFAULT_ROLLOVER_HOUR
    _ROLLOVER_CACHE[city] = hour
    return hour


def current_work_date(city: str, now: datetime | None = None) -> date:
    """Return the work date for `city` at `now` (defaults to wall clock).

    Naive datetimes are treated as UTC and converted; aware datetimes are
    converted to the city's local zone before the rollover-hour comparison.
    When local-hour < rollover_hour, the previous calendar day is returned.
    """
    tz = _tz_for_city(city)
    if now is None:
        now = datetime.now(tz)
    elif now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    local = now.astimezone(tz)
    rollover = _resolve_rollover_hour(city)
    if local.hour < rollover:
        return (local - timedelta(days=1)).date()
    return local.date()


def resolve_work_date(city: str, at: datetime) -> date:
    """Return the work date for `city` at `at` (aware datetime required).

    Thin wrapper over `current_work_date` that mirrors the ops helper's
    explicit-timestamp signature.
    """
    return current_work_date(city, now=at)


__all__ = [
    "DEFAULT_ROLLOVER_HOUR",
    "current_work_date",
    "resolve_work_date",
]

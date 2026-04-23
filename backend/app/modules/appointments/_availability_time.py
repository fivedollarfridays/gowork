"""Low-level time + DST helpers for the appointment availability engine.

Extracted from ``availability.py`` to keep that module under the 12-function
per-file limit. Purely functional, no module-level state.
"""

from __future__ import annotations

from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from app.modules.common.temporal_types import TIMEZONE_BY_CITY

__all__ = [
    "advance_cursor",
    "localize_or_none",
    "parse_hhmm",
    "tz_for_city",
]


def tz_for_city(city: str) -> ZoneInfo:
    """Resolve the IANA zone for a city slug; raises KeyError if unknown."""
    tz_name = TIMEZONE_BY_CITY.get(city)
    if tz_name is None:
        raise KeyError(f"No timezone configured for city {city!r}")
    return ZoneInfo(tz_name)


def parse_hhmm(value: str) -> time:
    """Parse ``"HH:MM"`` into a ``time`` object."""
    hh, mm = value.split(":")
    return time(int(hh), int(mm))


def localize_or_none(naive: datetime, tz: ZoneInfo) -> datetime | None:
    """Attach ``tz`` to ``naive`` datetime, returning None for a
    DST-nonexistent local time (spring-forward skipped hour).

    Compare ``fold=0`` and ``fold=1`` resolutions: if the offsets differ and
    the fold=0 UTC instant is *later* than fold=1, we're reading a skipped
    wall clock — the time never occurred, so return None.
    """
    d0 = naive.replace(tzinfo=tz, fold=0)
    d1 = naive.replace(tzinfo=tz, fold=1)
    if d0.utcoffset() == d1.utcoffset():
        return d0
    if d0.astimezone(timezone.utc) > d1.astimezone(timezone.utc):
        return None
    return d0


def advance_cursor(
    cursor_local: datetime, duration: timedelta, tz: ZoneInfo
) -> datetime | None:
    """Next slot start after cursor; skip past a DST-nonexistent landing.

    Walks forward in ``duration`` strides until a valid local time is found.
    Bounded by the DST gap size (typically 1h); 24 attempts tolerates even
    2h gaps with tiny strides before giving up.
    """
    naive = (cursor_local + duration).replace(tzinfo=None)
    for _ in range(24):
        nxt = localize_or_none(naive, tz)
        if nxt is not None:
            return nxt
        naive = naive + duration
    return None

"""Tests for app.core.day_boundary (T12.3).

Port of ops:lib/nightly_day_boundary.py semantics, city-generic. Verifies:
  * Work-date rollover (before rollover_hour → yesterday's work date)
  * Multi-city timezone lookup via TIMEZONE_BY_CITY registry
  * DST spring-forward / fall-back correctness
  * Rollover-hour resolution from city config w/ default fallback
"""

from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest

from app.core import day_boundary


@pytest.fixture(autouse=True)
def _clear_rollover_cache():
    """Ensure rollover-hour resolver cache is cleared per test."""
    if hasattr(day_boundary, "_rollover_cache_clear"):
        day_boundary._rollover_cache_clear()
    yield
    if hasattr(day_boundary, "_rollover_cache_clear"):
        day_boundary._rollover_cache_clear()


def test_current_work_date_before_rollover_returns_yesterday():
    """At 02:30 local, work_date should still be yesterday (rollover=4)."""
    ct = ZoneInfo("America/Chicago")
    now = datetime(2026, 4, 15, 2, 30, tzinfo=ct)
    assert day_boundary.current_work_date("montgomery", now=now) == date(2026, 4, 14)


def test_current_work_date_after_rollover_returns_today():
    """At 10:00 local, work_date is today."""
    ct = ZoneInfo("America/Chicago")
    now = datetime(2026, 4, 15, 10, 0, tzinfo=ct)
    assert day_boundary.current_work_date("montgomery", now=now) == date(2026, 4, 15)


def test_current_work_date_exactly_at_rollover_returns_today():
    """At exactly 04:00 (rollover hour), work_date rolls forward to today."""
    ct = ZoneInfo("America/Chicago")
    now = datetime(2026, 4, 15, 4, 0, tzinfo=ct)
    assert day_boundary.current_work_date("montgomery", now=now) == date(2026, 4, 15)


def test_dst_spring_forward():
    """On DST spring-forward (2026-03-08 US), 02:30 local is 'skipped'.

    We pass a UTC timestamp that converts to post-jump local time. Since
    2:30 AM CST is "lost", we use 03:30 CDT which in UTC is 08:30Z.
    Work date should still be 2026-03-07 because local hour (3) < 4.
    """
    utc_dt = datetime(2026, 3, 8, 8, 30, tzinfo=ZoneInfo("UTC"))
    # 08:30Z -> 03:30 America/Chicago (CDT, post-spring-forward). 3 < 4, yesterday.
    assert day_boundary.current_work_date("montgomery", now=utc_dt) == date(2026, 3, 7)


def test_dst_fall_back():
    """On DST fall-back (2026-11-01 US), 01:30 occurs twice.

    Use an unambiguous UTC timestamp that maps to 01:30 America/Chicago CST
    (after the fall-back, so 07:30Z). Local hour 1 < 4 → work date is 2026-10-31.
    """
    utc_dt = datetime(2026, 11, 1, 7, 30, tzinfo=ZoneInfo("UTC"))
    # 07:30Z on Nov 1 = 01:30 CST (UTC-6, post fall-back). 1 < 4, yesterday.
    assert day_boundary.current_work_date("montgomery", now=utc_dt) == date(2026, 10, 31)


def test_cross_city_different_tz(monkeypatch):
    """Same UTC instant produces different work_dates in different-TZ cities."""
    # Patch the registry so the two known cities live in different TZs.
    from app.modules.common import temporal_types as tt

    patched = dict(tt.TIMEZONE_BY_CITY)
    patched["montgomery"] = "America/New_York"  # ET
    patched["fort-worth"] = "America/Los_Angeles"  # PT
    monkeypatch.setattr(tt, "TIMEZONE_BY_CITY", patched)
    monkeypatch.setattr(day_boundary, "TIMEZONE_BY_CITY", patched)

    # 2026-04-15 05:00Z = 01:00 ET (yesterday per rollover) / 22:00 PT prev day.
    # ET: local=2026-04-15 01:00, hour 1 < 4 → 2026-04-14.
    # PT: local=2026-04-14 22:00, hour 22 ≥ 4 → 2026-04-14.
    # Pick a timestamp where the two diverge: 2026-04-15 10:00Z
    # ET: 06:00 → 2026-04-15. PT: 03:00 → 2026-04-14 (hour 3 < 4).
    utc = datetime(2026, 4, 15, 10, 0, tzinfo=ZoneInfo("UTC"))
    assert day_boundary.current_work_date("montgomery", now=utc) == date(2026, 4, 15)
    assert day_boundary.current_work_date("fort-worth", now=utc) == date(2026, 4, 14)


def test_resolve_rollover_hour_default():
    """Default rollover is 4 when city config does not specify one."""
    assert day_boundary._resolve_rollover_hour("montgomery") == 4


def test_resolve_rollover_hour_from_config(monkeypatch):
    """If city config exposes a rollover hour, helper returns it."""
    # Fake a city-config loader that returns a rollover_hour attribute.
    class _FakeCfg:
        rollover_hour = 5

    monkeypatch.setattr(
        day_boundary, "_load_city_config_for_rollover", lambda city: _FakeCfg()
    )
    assert day_boundary._resolve_rollover_hour("montgomery") == 5


def test_resolve_work_date_with_override():
    """resolve_work_date accepts a datetime and returns the work date."""
    ct = ZoneInfo("America/Chicago")
    at = datetime(2026, 4, 15, 9, 0, tzinfo=ct)
    assert day_boundary.resolve_work_date("montgomery", at=at) == date(2026, 4, 15)


def test_resolve_work_date_before_rollover():
    """resolve_work_date rolls back when at < rollover_hour."""
    ct = ZoneInfo("America/Chicago")
    at = datetime(2026, 4, 15, 3, 0, tzinfo=ct)
    assert day_boundary.resolve_work_date("montgomery", at=at) == date(2026, 4, 14)


def test_unknown_city_raises():
    """Requesting a city with no TZ mapping raises KeyError."""
    with pytest.raises(KeyError):
        day_boundary.current_work_date("atlantis")

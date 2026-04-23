"""Appointment availability engine (T12.8).

Port of `ops:lib/booking_availability.py` adapted to MontGoWork:

  * City timezone resolved via ``TIMEZONE_BY_CITY``.
  * Busy intervals derived from ``Appointment`` instances (starts_at/ends_at).
  * Worker unavailability injected via ``unavailability_blocks`` param (T12.8a
    will populate this; until then callers pass ``None`` or ``[]``).
  * Holidays attached to the ``ServiceConfig``.

Public API:
  * ``compute_available_slots(service, existing_appointments, *, city, day,
    unavailability_blocks=None) -> list[datetime]``
  * ``compute_availability_range(service, existing_appointments, *, city,
    start_day, days_out, unavailability_blocks=None) -> dict[date, list[datetime]]``

Algorithm per day:
  1. Skip if day-of-week is closed or day is a holiday.
  2. Build local-tz windows from ``service.hours_local``; resolve DST using
     ``localize_or_none`` (spring-forward -> skipped; fall-back -> unique
     UTC instants).
  3. Collect busy intervals (UTC) from existing appointments + unavailability.
  4. Walk each window in ``duration_minutes`` strides; emit candidates that
     don't intersect any busy interval.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

from app.modules.appointments.types import Appointment

from ._availability_time import (
    advance_cursor,
    localize_or_none,
    parse_hhmm,
    tz_for_city,
)
from .service_config import ServiceConfig

__all__ = ["compute_availability_range", "compute_available_slots"]


def _day_is_closed(day: date, service: ServiceConfig) -> bool:
    """True if the service is closed on ``day`` (weekday or holiday)."""
    return day.weekday() in service.closed_days_of_week or day in service.holidays


def _windows_for_day(
    day: date, service: ServiceConfig, tz: ZoneInfo
) -> list[tuple[datetime, datetime]]:
    """Build local tz-aware [start, end] windows for the day. Empty if closed
    or if DST makes all starts/ends nonexistent."""
    out: list[tuple[datetime, datetime]] = []
    for start_s, end_s in service.hours_local:
        start_local = localize_or_none(
            datetime.combine(day, parse_hhmm(start_s)), tz
        )
        end_local = localize_or_none(datetime.combine(day, parse_hhmm(end_s)), tz)
        if start_local is None or end_local is None:
            continue
        if end_local <= start_local:
            continue
        out.append((start_local, end_local))
    return out


def _appointment_busy_intervals(
    appointments: list[Appointment],
) -> list[tuple[datetime, datetime]]:
    """Extract (start_utc, end_utc) intervals from booked appointments."""
    out: list[tuple[datetime, datetime]] = []
    for appt in appointments:
        if appt.starts_at is None or appt.ends_at is None:
            continue
        out.append(
            (
                appt.starts_at.astimezone(timezone.utc),
                appt.ends_at.astimezone(timezone.utc),
            )
        )
    return out


def _recurring_block_for_day(
    block: dict[str, Any], day: date, tz: ZoneInfo
) -> tuple[datetime, datetime] | None:
    """Resolve a recurring unavailability block ``{day_of_week, start_time,
    end_time}`` to a UTC interval on ``day``, or None if it doesn't apply."""
    if int(block["day_of_week"]) != day.weekday():
        return None
    start_local = localize_or_none(
        datetime.combine(day, parse_hhmm(block["start_time"])), tz
    )
    end_local = localize_or_none(
        datetime.combine(day, parse_hhmm(block["end_time"])), tz
    )
    if start_local is None or end_local is None or end_local <= start_local:
        return None
    return (
        start_local.astimezone(timezone.utc),
        end_local.astimezone(timezone.utc),
    )


def _oneoff_block_for_day(
    block: dict[str, Any], day: date, tz: ZoneInfo
) -> tuple[datetime, datetime] | None:
    """Resolve a one-off ``{start, end}`` unavailability block to UTC, keeping
    only blocks that intersect ``day`` in the city's local tz."""
    s: datetime = block["start"]
    e: datetime = block["end"]
    if s.tzinfo is None or e.tzinfo is None or e <= s:
        return None
    s_utc = s.astimezone(timezone.utc)
    e_utc = e.astimezone(timezone.utc)
    day_start = datetime.combine(day, time(0, 0)).replace(tzinfo=tz)
    day_end = day_start + timedelta(days=1)
    if e_utc <= day_start.astimezone(timezone.utc):
        return None
    if s_utc >= day_end.astimezone(timezone.utc):
        return None
    return (s_utc, e_utc)


def _unavailability_for_day(
    blocks: list[dict[str, Any]] | None,
    day: date,
    tz: ZoneInfo,
) -> list[tuple[datetime, datetime]]:
    """Translate recurring + one-off unavailability blocks into UTC intervals
    for ``day``."""
    if not blocks:
        return []
    out: list[tuple[datetime, datetime]] = []
    for block in blocks:
        if "day_of_week" in block:
            interval = _recurring_block_for_day(block, day, tz)
        elif "start" in block and "end" in block:
            interval = _oneoff_block_for_day(block, day, tz)
        else:
            interval = None
        if interval is not None:
            out.append(interval)
    return out


def _intersects_busy(
    slot_start_utc: datetime,
    slot_end_utc: datetime,
    busy: list[tuple[datetime, datetime]],
) -> bool:
    """True if [slot_start, slot_end) overlaps any busy interval."""
    for b_start, b_end in busy:
        if b_end > slot_start_utc and b_start < slot_end_utc:
            return True
    return False


def _walk_window(
    win_start_local: datetime,
    win_end_local: datetime,
    duration: timedelta,
    busy: list[tuple[datetime, datetime]],
    tz: ZoneInfo,
) -> list[datetime]:
    """Walk one local window, returning available slot start times (tz-aware)."""
    slots: list[datetime] = []
    cursor = win_start_local
    max_iter = int((win_end_local - win_start_local).total_seconds() // 60) + 10
    for _ in range(max_iter):
        slot_end_local = cursor + duration
        if slot_end_local > win_end_local:
            break
        start_utc = cursor.astimezone(timezone.utc)
        end_utc = slot_end_local.astimezone(timezone.utc)
        if not _intersects_busy(start_utc, end_utc, busy):
            slots.append(cursor)
        nxt = advance_cursor(cursor, duration, tz)
        if nxt is None:
            break
        cursor = nxt
    return slots


def compute_available_slots(
    service: ServiceConfig,
    existing_appointments: list[Appointment],
    *,
    city: str,
    day: date,
    unavailability_blocks: list[dict[str, Any]] | None = None,
) -> list[datetime]:
    """Return tz-aware datetimes when ``service`` is available on ``day``.

    Subtracts existing appointments and any unavailability blocks that apply.
    Returns ``[]`` on closed days or holidays. DST-aware: skipped-hour
    candidates are omitted; fall-back yields unique UTC instants.
    """
    tz = tz_for_city(city)
    if _day_is_closed(day, service):
        return []
    windows = _windows_for_day(day, service, tz)
    if not windows:
        return []
    duration = timedelta(minutes=service.duration_minutes)
    busy = _appointment_busy_intervals(existing_appointments)
    busy.extend(_unavailability_for_day(unavailability_blocks, day, tz))
    out: list[datetime] = []
    for win_start, win_end in windows:
        out.extend(_walk_window(win_start, win_end, duration, busy, tz))
    return out


def compute_availability_range(
    service: ServiceConfig,
    existing_appointments: list[Appointment],
    *,
    city: str,
    start_day: date,
    days_out: int,
    unavailability_blocks: list[dict[str, Any]] | None = None,
) -> dict[date, list[datetime]]:
    """Per-day availability for ``days_out`` days starting ``start_day``."""
    if days_out < 0:
        raise ValueError("days_out must be non-negative")
    out: dict[date, list[datetime]] = {}
    for offset in range(days_out):
        day = start_day + timedelta(days=offset)
        out[day] = compute_available_slots(
            service,
            existing_appointments,
            city=city,
            day=day,
            unavailability_blocks=unavailability_blocks,
        )
    return out

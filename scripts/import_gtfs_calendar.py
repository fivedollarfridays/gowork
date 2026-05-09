"""Calendar / service-id helpers for the GTFS importer.

Kept in a separate module so scripts/import_gtfs.py stays under arch limits.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date

WEEKDAY_FLAGS = ("monday", "tuesday", "wednesday", "thursday", "friday")
_DAY_FLAG_NAMES = (
    "monday", "tuesday", "wednesday", "thursday",
    "friday", "saturday", "sunday",
)


def derive_flags_from_calendar_dates(
    calendar_dates: list[dict],
) -> dict[str, dict]:
    """Synthesize calendar.txt-shaped rows from calendar_dates.txt entries.

    Some agencies (DART) put the bulk of operating days in calendar_dates.txt
    rather than the repeating M-F pattern in calendar.txt. For each
    service_id, walk the date entries with ``exception_type == "1"`` (service
    runs that day), derive day-of-week flags, and emit a row with the same
    shape calendar.txt would produce. Service_ids present in calendar.txt
    take precedence over derived rows (see index_calendar merge order).
    """
    days_by_svc: dict[str, set[int]] = defaultdict(set)
    for row in calendar_dates:
        if row.get("exception_type") != "1":
            continue
        d = (row.get("date") or "").strip()
        if len(d) != 8 or not d.isdigit():
            continue
        dt = date(int(d[:4]), int(d[4:6]), int(d[6:8]))
        days_by_svc[row["service_id"]].add(dt.weekday())
    return {
        sid: {
            "service_id": sid,
            **{
                _DAY_FLAG_NAMES[i]: ("1" if i in days else "0")
                for i in range(7)
            },
        }
        for sid, days in days_by_svc.items()
    }


def index_calendar(
    calendar: list[dict],
    calendar_dates: list[dict] | None = None,
) -> dict[str, dict]:
    """Index calendar.txt rows by service_id, merging calendar_dates derives.

    Service_ids defined in calendar.txt take precedence — calendar.txt is the
    authoritative repeating pattern. Derived rows from calendar_dates.txt only
    cover service_ids absent from calendar.txt (DART's pattern).
    """
    out = {row["service_id"]: row for row in calendar}
    if calendar_dates:
        for sid, derived in derive_flags_from_calendar_dates(calendar_dates).items():
            out.setdefault(sid, derived)
    return out


def service_runs_weekday(cal_row: dict) -> bool:
    """True if the service runs on at least one Mon-Fri day."""
    return any(cal_row.get(flag) == "1" for flag in WEEKDAY_FLAGS)


def to_minutes(gtfs_time: str) -> int:
    """Parse a GTFS HH:MM[:SS] time into minutes-since-midnight.

    GTFS allows times >= 24:00 (e.g. ``25:30:00``) to express next-day
    service; we keep the over-24 value here and let ``from_minutes``
    wrap with ``% 24`` when formatting back to display HH:MM.
    """
    parts = gtfs_time.strip().split(":")
    return int(parts[0]) * 60 + int(parts[1])


def from_minutes(total: int) -> str:
    """Format minutes-since-midnight as ``HH:MM`` in the 00-23 range."""
    return f"{(total // 60) % 24:02d}:{total % 60:02d}"


def weekday_service_ids(cal_index: dict[str, dict]) -> set[str]:
    return {sid for sid, row in cal_index.items() if service_runs_weekday(row)}


def route_runs_on(
    day_flag: str,
    route_id: str,
    trips: list[dict],
    cal_index: dict[str, dict],
) -> bool:
    """True if ANY service_id used by `route_id` has `day_flag` (e.g.
    "saturday") set. Mirrors the weekday-window derivation philosophy:
    sat/sun must NOT be read from the primary service alone, since the
    primary is whichever service has the most trips (often weekdays) and
    its flags don't reflect weekend service that lives in a separate
    service_id (DART pattern: weekdays via calendar_dates.txt, Sat via
    service_id 3, Sun via service_id 4 — three separate services per route).
    """
    for trip in trips:
        if trip["route_id"] != route_id:
            continue
        sid = trip["service_id"]
        cal = cal_index.get(sid)
        if cal is not None and cal.get(day_flag) == "1":
            return True
    return False


def weekday_trip_ids_for_route(
    route_id: str, trips: list[dict], wkday_sids: set[str]
) -> set[str]:
    return {
        trip["trip_id"]
        for trip in trips
        if trip["route_id"] == route_id and trip["service_id"] in wkday_sids
    }


def stop_time_minute_bounds(
    stop_times: list[dict], allowed_trip_ids: set[str]
) -> tuple[int, int] | None:
    """Return (min_minutes, max_minutes) across both arrival/departure cols."""
    minutes_min: int | None = None
    minutes_max: int | None = None
    for st in stop_times:
        if st["trip_id"] not in allowed_trip_ids:
            continue
        for col in ("departure_time", "arrival_time"):
            val = st.get(col)
            if not val:
                continue
            mins = to_minutes(val)
            if minutes_min is None or mins < minutes_min:
                minutes_min = mins
            if minutes_max is None or mins > minutes_max:
                minutes_max = mins
    if minutes_min is None or minutes_max is None:
        return None
    return minutes_min, minutes_max


def derive_weekday_window(
    route_id: str,
    trips: list[dict],
    stop_times: list[dict],
    cal_index: dict[str, dict],
) -> tuple[str, str]:
    """(weekday_start, weekday_end) MIN/MAX over weekday-service stop_times."""
    wkday_sids = weekday_service_ids(cal_index)
    wkday_trips = weekday_trip_ids_for_route(route_id, trips, wkday_sids)
    if not wkday_trips:
        return "00:00", "00:00"
    bounds = stop_time_minute_bounds(stop_times, wkday_trips)
    if bounds is None:
        return "00:00", "00:00"
    return from_minutes(bounds[0]), from_minutes(bounds[1])

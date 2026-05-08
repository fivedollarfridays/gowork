"""Calendar / service-id helpers for the GTFS importer.

Kept in a separate module so scripts/import_gtfs.py stays under arch limits.
"""

from __future__ import annotations

WEEKDAY_FLAGS = ("monday", "tuesday", "wednesday", "thursday", "friday")


def index_calendar(calendar: list[dict]) -> dict[str, dict]:
    """Index calendar.txt rows by service_id."""
    return {row["service_id"]: row for row in calendar}


def service_runs_weekday(cal_row: dict) -> bool:
    """True if the service runs on at least one Mon-Fri day."""
    return any(cal_row.get(flag) == "1" for flag in WEEKDAY_FLAGS)


def select_primary_service(
    route_id: str, trips: list[dict], cal_index: dict[str, dict]
) -> str | None:
    """Pick the service_id with the most trips for this route.

    Tie-breaker: alphabetical service_id (deterministic). Returns None if no
    trips are scheduled for the route.
    """
    counts: dict[str, int] = {}
    for trip in trips:
        if trip["route_id"] != route_id:
            continue
        sid = trip["service_id"]
        if sid not in cal_index:
            continue
        counts[sid] = counts.get(sid, 0) + 1
    if not counts:
        return None
    return min(counts.keys(), key=lambda sid: (-counts[sid], sid))


def to_minutes(gtfs_time: str) -> int:
    parts = gtfs_time.strip().split(":")
    return int(parts[0]) * 60 + int(parts[1])


def from_minutes(total: int) -> str:
    return f"{(total // 60) % 24:02d}:{total % 60:02d}"


def weekday_service_ids(cal_index: dict[str, dict]) -> set[str]:
    return {sid for sid, row in cal_index.items() if service_runs_weekday(row)}


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

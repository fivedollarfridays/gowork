"""Stop ordering / indexing helpers for the GTFS importer."""

from __future__ import annotations


def index_trips_by_route(trips: list[dict]) -> dict[str, list[str]]:
    by_route: dict[str, list[str]] = {}
    for trip in trips:
        by_route.setdefault(trip["route_id"], []).append(trip["trip_id"])
    return by_route


def index_stop_times_by_trip(stop_times: list[dict]) -> dict[str, list[dict]]:
    by_trip: dict[str, list[dict]] = {}
    for st in stop_times:
        by_trip.setdefault(st["trip_id"], []).append(st)
    for rows in by_trip.values():
        rows.sort(key=lambda r: int(r["stop_sequence"]))
    return by_trip


def ordered_stops_for_route(
    route_id: str,
    trips_by_route: dict[str, list[str]],
    stop_times_by_trip: dict[str, list[dict]],
) -> list[str]:
    """De-duplicated stop_ids in canonical visit order for a route."""
    trip_ids = sorted(trips_by_route.get(route_id, []))
    seen: set[str] = set()
    ordered: list[str] = []
    for trip_id in trip_ids:
        for st in stop_times_by_trip.get(trip_id, []):
            sid = st["stop_id"]
            if sid in seen:
                continue
            seen.add(sid)
            ordered.append(sid)
    return ordered


def route_number_from_row(row: dict, fallback_index: int) -> int:
    """Derive integer route_number from a GTFS routes.txt row."""
    raw_short = (row.get("route_short_name") or "").strip()
    if raw_short.isdigit():
        return int(raw_short)
    rid = (row.get("route_id") or "").strip()
    digits = "".join(ch for ch in rid if ch.isdigit())
    if digits:
        return int(digits)
    return fallback_index


def route_name_from_row(row: dict) -> str:
    long_name = (row.get("route_long_name") or "").strip()
    if long_name:
        return long_name
    short = (row.get("route_short_name") or "").strip()
    return short or (row.get("route_id") or "").strip()

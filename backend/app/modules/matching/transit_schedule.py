"""Transit schedule matcher — route-aware feasibility for M-Transit."""

from urllib.parse import quote

from app.modules.matching.scoring import haversine_miles
from app.modules.matching.types_transit import RouteFeasibility, TransitInfo, TransitWarning

_SHIFT_HOURS = {"daytime": (8, 17), "evening": (16, 24), "night": (22, 6)}
LONG_WALK_THRESHOLD = 0.5
DEFAULT_MAX_WALK = 1.0


def schedule_hours_for(schedule_type: str) -> tuple[int, int] | None:
    """Return (shift_start, shift_end) hours, or None for flexible."""
    return _SHIFT_HOURS.get(schedule_type)


def find_serving_routes(
    lat: float, lng: float, stops_with_routes: list[dict],
    max_walk_miles: float = DEFAULT_MAX_WALK,
) -> list[RouteFeasibility]:
    """Find routes within walk distance. One per route (closest stop wins)."""
    best: dict[int, tuple[float, dict]] = {}
    for stop in stops_with_routes:
        dist = haversine_miles(lat, lng, stop["lat"], stop["lng"])
        if dist > max_walk_miles:
            continue
        rid = stop["route_id"]
        if rid not in best or dist < best[rid][0]:
            best[rid] = (dist, stop)

    return [
        RouteFeasibility(
            route_number=s["route_number"], route_name=s["route_name"],
            nearest_stop=s["stop_name"], walk_miles=round(d, 2),
            first_bus=s["weekday_start"], last_bus=s["weekday_end"],
            has_sunday=bool(s.get("sunday")), feasible=True,
        )
        for d, s in sorted(best.values(), key=lambda x: x[0])
    ]


def check_schedule_feasibility(
    shift_start: int, shift_end: int, route: dict,
) -> tuple[bool, list[TransitWarning]]:
    """Check if route hours cover a shift. End < start means overnight."""
    warnings: list[TransitWarning] = []
    first, last = _parse_hour(route["weekday_start"]), _parse_hour(route["weekday_end"])
    if not route.get("sunday"):
        warnings.append(TransitWarning.SUNDAY_GAP)
    feasible = True
    if shift_end < shift_start:  # overnight
        if shift_start > last or shift_end < first:
            feasible, _ = False, warnings.append(TransitWarning.NIGHT_GAP)
    elif shift_start < first or shift_end > last:
        feasible = False
        if TransitWarning.NIGHT_GAP not in warnings:
            warnings.append(TransitWarning.NIGHT_GAP)
    return feasible, warnings


def detect_transfer_count(user_route_ids: set[int], job_route_ids: set[int]) -> int:
    """0 if shared route, 1 if transfer at Rosa Parks hub needed."""
    if not user_route_ids or not job_route_ids:
        return 0
    return 0 if user_route_ids & job_route_ids else 1


def build_transit_info(
    job_lat: float, job_lng: float,
    stops_with_routes: list[dict],
    shift_start: int | None = None,
    shift_end: int | None = None,
    user_lat: float | None = None,
    user_lng: float | None = None,
    max_walk_miles: float = DEFAULT_MAX_WALK,
) -> TransitInfo:
    """Build complete transit info for a job location."""
    serving = find_serving_routes(job_lat, job_lng, stops_with_routes, max_walk_miles)
    warnings = _check_warnings(serving, shift_start, shift_end)
    transfer_count = _compute_transfers(
        serving, stops_with_routes, user_lat, user_lng, max_walk_miles, warnings,
    )

    maps_url = (
        google_maps_transit_url(user_lat, user_lng, job_lat, job_lng)
        if user_lat is not None and user_lng is not None else None
    )
    return TransitInfo(
        serving_routes=serving, transfer_count=transfer_count,
        warnings=warnings, google_maps_url=maps_url,
    )


def _check_warnings(
    serving: list[RouteFeasibility], shift_start: int | None, shift_end: int | None,
) -> list[TransitWarning]:
    warnings: list[TransitWarning] = []
    if shift_start is not None and shift_end is not None:
        for r in serving:
            rd = {"weekday_start": r.first_bus, "weekday_end": r.last_bus, "sunday": r.has_sunday}
            ok, rw = check_schedule_feasibility(shift_start, shift_end, rd)
            r.feasible = ok
            for w in rw:
                if w not in warnings:
                    warnings.append(w)
    if serving and serving[0].walk_miles > LONG_WALK_THRESHOLD:
        if TransitWarning.LONG_WALK not in warnings:
            warnings.append(TransitWarning.LONG_WALK)
    return warnings


def _compute_transfers(
    job_serving: list[RouteFeasibility], stops: list[dict],
    user_lat: float | None, user_lng: float | None,
    max_walk: float, warnings: list[TransitWarning],
) -> int:
    if user_lat is None or user_lng is None:
        return 0
    ur = find_serving_routes(user_lat, user_lng, stops, max_walk)
    count = detect_transfer_count({r.route_number for r in ur}, {r.route_number for r in job_serving})
    if count > 0 and TransitWarning.TRANSFER_REQUIRED not in warnings:
        warnings.append(TransitWarning.TRANSFER_REQUIRED)
    return count


def google_maps_transit_url(
    origin_lat: float, origin_lng: float,
    dest_lat: float, dest_lng: float,
) -> str:
    """Generate a Google Maps directions URL with transit mode."""
    origin = f"{origin_lat},{origin_lng}"
    dest = f"{dest_lat},{dest_lng}"
    return f"https://www.google.com/maps/dir/{quote(origin)}/{quote(dest)}?travelmode=transit"


def _parse_hour(time_str: str) -> int:
    """Parse 'HH:MM' to integer hour."""
    return int(time_str.split(":")[0])

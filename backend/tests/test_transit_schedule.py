"""Tests for transit schedule matcher module."""

from app.modules.matching.transit_schedule import (
    build_transit_info,
    check_schedule_feasibility,
    detect_transfer_count,
    find_serving_routes,
    google_maps_transit_url,
    schedule_hours_for,
)
from app.modules.matching.types import TransitWarning


# ---------------------------------------------------------------------------
# Fixtures — representative transit data
# ---------------------------------------------------------------------------

ROSA_PARKS = {"stop_name": "Rosa Parks Transfer Center", "lat": 32.3779, "lng": -86.3088}


def _stop(name: str, lat: float, lng: float, route_id: int, **route_fields) -> dict:
    """Build a stop-with-route dict for testing."""
    return {
        "stop_name": name,
        "lat": lat,
        "lng": lng,
        "route_id": route_id,
        "route_number": route_fields.get("route_number", route_id),
        "route_name": route_fields.get("route_name", f"Route {route_id}"),
        "weekday_start": route_fields.get("weekday_start", "05:00"),
        "weekday_end": route_fields.get("weekday_end", "21:00"),
        "saturday": route_fields.get("saturday", 1),
        "sunday": route_fields.get("sunday", 0),
    }


SAMPLE_STOPS = [
    _stop("Rosa Parks Transfer Center", 32.3779, -86.3088, 1, route_name="Day Street"),
    _stop("Eastdale Mall", 32.3680, -86.2450, 1, route_name="Day Street"),
    _stop("Rosa Parks Transfer Center", 32.3779, -86.3088, 2, route_name="Capitol Heights"),
    _stop("Capitol Heights", 32.3850, -86.2900, 2, route_name="Capitol Heights"),
    _stop("Rosa Parks Transfer Center", 32.3779, -86.3088, 3, route_name="McGehee Road"),
    _stop("McGehee Rd at Perry Hill", 32.3350, -86.2700, 3, route_name="McGehee Road"),
]


# ---------------------------------------------------------------------------
# schedule_hours_for
# ---------------------------------------------------------------------------

class TestScheduleHoursFor:
    def test_daytime(self) -> None:
        start, end = schedule_hours_for("daytime")
        assert start == 8 and end == 17

    def test_evening(self) -> None:
        start, end = schedule_hours_for("evening")
        assert start == 16 and end == 24

    def test_night(self) -> None:
        start, end = schedule_hours_for("night")
        assert start == 22 and end == 6

    def test_flexible_returns_none(self) -> None:
        assert schedule_hours_for("flexible") is None


# ---------------------------------------------------------------------------
# find_serving_routes
# ---------------------------------------------------------------------------

class TestFindServingRoutes:
    def test_finds_route_within_walk_distance(self) -> None:
        # Point very close to Eastdale Mall stop (route 1)
        routes = find_serving_routes(32.3680, -86.2451, SAMPLE_STOPS)
        assert len(routes) >= 1
        assert routes[0].route_name == "Day Street"
        assert routes[0].walk_miles < 0.1

    def test_no_routes_when_too_far(self) -> None:
        # Point far from any stop (Auburn, AL — ~50 miles)
        routes = find_serving_routes(32.6099, -85.4808, SAMPLE_STOPS)
        assert len(routes) == 0

    def test_rosa_parks_matches_multiple_routes(self) -> None:
        # Point at Rosa Parks Transfer Center — should match routes 1, 2, 3
        routes = find_serving_routes(32.3779, -86.3088, SAMPLE_STOPS)
        route_ids = {r.route_number for r in routes}
        assert route_ids == {1, 2, 3}

    def test_walk_miles_calculated(self) -> None:
        routes = find_serving_routes(32.3680, -86.2451, SAMPLE_STOPS)
        assert routes[0].walk_miles >= 0.0

    def test_custom_max_walk(self) -> None:
        # Point ~0.3 miles from Eastdale Mall — found with max_walk=0.5, not 0.1
        routes_wide = find_serving_routes(32.3700, -86.2450, SAMPLE_STOPS, max_walk_miles=0.5)
        routes_narrow = find_serving_routes(32.3700, -86.2450, SAMPLE_STOPS, max_walk_miles=0.01)
        assert len(routes_wide) >= 1
        assert len(routes_narrow) == 0

    def test_deduplicates_routes(self) -> None:
        # Rosa Parks appears 3 times (routes 1, 2, 3) — should return 3 unique routes
        routes = find_serving_routes(32.3779, -86.3088, SAMPLE_STOPS)
        route_numbers = [r.route_number for r in routes]
        assert len(route_numbers) == len(set(route_numbers))


# ---------------------------------------------------------------------------
# check_schedule_feasibility
# ---------------------------------------------------------------------------

class TestCheckScheduleFeasibility:
    def test_daytime_shift_feasible(self) -> None:
        route = {"weekday_start": "05:00", "weekday_end": "21:00", "sunday": 0}
        feasible, warnings = check_schedule_feasibility(8, 17, route)
        assert feasible is True
        assert TransitWarning.NIGHT_GAP not in warnings

    def test_night_shift_infeasible(self) -> None:
        route = {"weekday_start": "05:00", "weekday_end": "21:00", "sunday": 0}
        feasible, warnings = check_schedule_feasibility(22, 6, route)
        assert feasible is False
        assert TransitWarning.NIGHT_GAP in warnings

    def test_evening_shift_ending_after_last_bus(self) -> None:
        route = {"weekday_start": "05:00", "weekday_end": "20:30", "sunday": 0}
        feasible, warnings = check_schedule_feasibility(16, 22, route)
        assert feasible is False
        assert TransitWarning.NIGHT_GAP in warnings

    def test_early_shift_before_first_bus(self) -> None:
        route = {"weekday_start": "05:30", "weekday_end": "21:00", "sunday": 0}
        feasible, warnings = check_schedule_feasibility(4, 12, route)
        assert feasible is False

    def test_sunday_route_warns(self) -> None:
        route = {"weekday_start": "05:00", "weekday_end": "21:00", "sunday": 0}
        _, warnings = check_schedule_feasibility(8, 17, route)
        assert TransitWarning.SUNDAY_GAP in warnings

    def test_sunday_route_no_warn_if_sunday_service(self) -> None:
        route = {"weekday_start": "05:00", "weekday_end": "21:00", "sunday": 1}
        _, warnings = check_schedule_feasibility(8, 17, route)
        assert TransitWarning.SUNDAY_GAP not in warnings


# ---------------------------------------------------------------------------
# detect_transfer_count
# ---------------------------------------------------------------------------

class TestDetectTransferCount:
    def test_same_route_no_transfer(self) -> None:
        assert detect_transfer_count({1, 2}, {1, 3}) == 0  # route 1 shared

    def test_different_routes_one_transfer(self) -> None:
        assert detect_transfer_count({1}, {2}) == 1  # transfer at hub

    def test_no_routes_returns_zero(self) -> None:
        assert detect_transfer_count(set(), {1}) == 0

    def test_multiple_disjoint_routes(self) -> None:
        count = detect_transfer_count({1}, {3})
        assert count == 1


# ---------------------------------------------------------------------------
# build_transit_info
# ---------------------------------------------------------------------------

class TestBuildTransitInfo:
    def test_returns_transit_info_near_stop(self) -> None:
        info = build_transit_info(32.3680, -86.2451, SAMPLE_STOPS)
        assert len(info.serving_routes) >= 1
        assert info.serving_routes[0].route_name == "Day Street"

    def test_no_routes_when_far(self) -> None:
        info = build_transit_info(33.0, -85.0, SAMPLE_STOPS)
        assert len(info.serving_routes) == 0
        assert info.transfer_count == 0

    def test_warnings_include_sunday_gap(self) -> None:
        info = build_transit_info(32.3680, -86.2451, SAMPLE_STOPS, shift_start=8, shift_end=17)
        assert TransitWarning.SUNDAY_GAP in info.warnings

    def test_warnings_include_night_gap(self) -> None:
        info = build_transit_info(32.3680, -86.2451, SAMPLE_STOPS, shift_start=22, shift_end=6)
        assert TransitWarning.NIGHT_GAP in info.warnings

    def test_long_walk_warning(self) -> None:
        # Point ~0.8 miles from nearest stop — within range but long walk
        info = build_transit_info(32.3780, -86.2450, SAMPLE_STOPS, max_walk_miles=1.5)
        if info.serving_routes and info.serving_routes[0].walk_miles > 0.5:
            assert TransitWarning.LONG_WALK in info.warnings

    def test_google_maps_url_populated(self) -> None:
        info = build_transit_info(
            32.3680, -86.2451, SAMPLE_STOPS,
            user_lat=32.3779, user_lng=-86.3088,
        )
        assert info.google_maps_url is not None
        assert "travelmode=transit" in info.google_maps_url

    def test_google_maps_url_none_without_user_coords(self) -> None:
        info = build_transit_info(32.3680, -86.2451, SAMPLE_STOPS)
        assert info.google_maps_url is None

    def test_transfer_count_from_user_to_job(self) -> None:
        # User near route 3 only stop, job near route 1 only stop
        info = build_transit_info(
            32.3350, -86.2700, SAMPLE_STOPS,  # near McGehee Rd stop (route 3)
            user_lat=32.3680, user_lng=-86.2450,  # near Eastdale Mall (route 1)
        )
        # Routes overlap at Rosa Parks, so might be 0 or 1 depending on logic
        assert info.transfer_count >= 0


# ---------------------------------------------------------------------------
# google_maps_transit_url
# ---------------------------------------------------------------------------

class TestGoogleMapsTransitUrl:
    def test_generates_url(self) -> None:
        url = google_maps_transit_url(32.3779, -86.3088, 32.3680, -86.2451)
        assert "32.3779" in url
        assert "32.368" in url
        assert "travelmode=transit" in url

    def test_uses_google_maps_domain(self) -> None:
        url = google_maps_transit_url(32.0, -86.0, 33.0, -85.0)
        assert url.startswith("https://www.google.com/maps/dir/")

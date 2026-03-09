"""Tests for commute time estimator module."""

import pytest

from app.modules.matching.commute_estimator import estimate_commute
from app.modules.matching.types_transit import (
    CommuteEstimate,
    RouteFeasibility,
    TransitInfo,
)


# ---------------------------------------------------------------------------
# Drive time tests
# ---------------------------------------------------------------------------


class TestDriveTime:
    """Drive time: distance_miles / 25 * 60, minimum 1 min."""

    def test_close_job_drive_time(self):
        """Job <1mi away -> drive ~2-3 min."""
        # 36104 and 36107 are close ZIPs in Montgomery
        result = estimate_commute(user_zip="36104", job_location="Montgomery, AL 36107")
        assert isinstance(result, CommuteEstimate)
        assert 1 <= result.drive_min <= 5

    def test_medium_job_drive_time(self):
        """Job ~5mi away -> drive ~12 min."""
        # 36104 (downtown) to 36117 (east Montgomery) ~5-6mi
        result = estimate_commute(user_zip="36104", job_location="Montgomery, AL 36117")
        assert 8 <= result.drive_min <= 18

    def test_far_job_drive_time(self):
        """Job ~15mi away -> drive ~36 min."""
        # Use a job location with unknown ZIP so it falls back to downtown,
        # then use a ZIP far from downtown. 36116 to downtown is ~6-7mi.
        # For a truly far job we need larger distance. Let's verify the formula
        # directly: 15 mi / 25 mph * 60 = 36 min.
        # 36117 to 36108: roughly 10+ miles
        result = estimate_commute(user_zip="36117", job_location="Montgomery, AL 36108")
        assert result.drive_min >= 15

    def test_minimum_drive_time_is_one(self):
        """Same location should give minimum 1 min drive."""
        result = estimate_commute(user_zip="36104", job_location="Montgomery, AL 36104")
        assert result.drive_min >= 1


# ---------------------------------------------------------------------------
# Walk time tests
# ---------------------------------------------------------------------------


class TestWalkTime:
    """Walk time: distance / 3 * 60, only if distance <= 2.0 miles."""

    def test_walk_time_within_2_miles(self):
        """1.5mi -> walk ~30 min. Use close ZIPs for short distance."""
        # 36104 to 36107 is ~1.2 mi — should be walkable
        result = estimate_commute(user_zip="36104", job_location="Montgomery, AL 36107")
        assert result.walk_min is not None
        assert 10 <= result.walk_min <= 50

    def test_walk_time_beyond_2_miles(self):
        """5mi -> walk is None."""
        # 36104 to 36117 is ~5-6mi — not walkable
        result = estimate_commute(user_zip="36104", job_location="Montgomery, AL 36117")
        assert result.walk_min is None

    def test_walk_time_same_zip(self):
        """Same ZIP -> walk time should be at minimum 1 min."""
        result = estimate_commute(user_zip="36104", job_location="Montgomery, AL 36104")
        # Same ZIP centroid = 0 distance, but minimum is 1 min
        assert result.walk_min is not None
        assert result.walk_min >= 1


# ---------------------------------------------------------------------------
# Transit time tests
# ---------------------------------------------------------------------------


def _make_transit_info(
    walk_miles: float = 0.3,
    has_routes: bool = True,
) -> TransitInfo:
    """Helper to build TransitInfo with or without serving routes."""
    routes = []
    if has_routes:
        routes.append(RouteFeasibility(
            route_number=4,
            route_name="Atlanta Hwy",
            nearest_stop="Court Square Transfer Center",
            walk_miles=walk_miles,
            first_bus="05:00",
            last_bus="21:00",
            has_sunday=False,
            feasible=True,
        ))
    return TransitInfo(serving_routes=routes)


class TestTransitTime:
    """Transit: walk_to_stop + 10 wait + ride + 5 walk_from_stop."""

    def test_transit_time_with_routes(self):
        """Transit info with serving routes -> transit time computed."""
        info = _make_transit_info(walk_miles=0.3)
        result = estimate_commute(
            user_zip="36104",
            job_location="Montgomery, AL 36107",
            transit_info=info,
        )
        assert result.transit_min is not None
        # walk_to_stop: 0.3/3*60 = 6 min -> round = 6
        # wait: 10
        # ride: dist/12*60 (dist ~1.2mi -> ~6 min)
        # walk_from_stop: 5
        # Total: ~27
        assert result.transit_min >= 20

    def test_transit_time_without_routes(self):
        """No transit_info -> transit_min is None."""
        result = estimate_commute(
            user_zip="36104",
            job_location="Montgomery, AL 36107",
            transit_info=None,
        )
        assert result.transit_min is None

    def test_transit_time_no_serving_routes(self):
        """Transit info with empty routes -> transit_min is None."""
        info = _make_transit_info(has_routes=False)
        result = estimate_commute(
            user_zip="36104",
            job_location="Montgomery, AL 36107",
            transit_info=info,
        )
        assert result.transit_min is None

    def test_transit_time_includes_walk_wait_ride_components(self):
        """Verify transit time includes all components."""
        info = _make_transit_info(walk_miles=0.5)
        result = estimate_commute(
            user_zip="36104",
            job_location="Montgomery, AL 36104",
            transit_info=info,
        )
        assert result.transit_min is not None
        # At minimum: walk_to_stop(1) + wait(10) + ride(1) + walk_from(5) = 17
        assert result.transit_min >= 17


# ---------------------------------------------------------------------------
# Edge case tests
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Same ZIP, unknown ZIP, and other edge cases."""

    def test_same_zip_minimal_commute(self):
        """Same ZIP -> drive ~1 min minimum."""
        result = estimate_commute(user_zip="36104", job_location="Montgomery, AL 36104")
        assert result.drive_min >= 1
        # Same centroid -> 0 miles, walk should still be min 1
        assert result.walk_min is not None
        assert result.walk_min >= 1

    def test_unknown_zip_uses_downtown(self):
        """Unknown ZIP falls back to downtown Montgomery coords."""
        # 99999 is not in ZIP_CENTROIDS -> falls back to DOWNTOWN_MONTGOMERY
        # Job with unknown ZIP also falls back to DOWNTOWN_MONTGOMERY
        # So unknown user + unknown job = same point = drive 1 min
        result = estimate_commute(user_zip="99999", job_location="Some Place, AL 99998")
        # Both fall back to downtown -> distance is 0 -> drive 1 min
        assert result.drive_min == 1
        assert result.walk_min == 1

    def test_unknown_user_zip_known_job_zip(self):
        """Unknown user ZIP falls back to downtown, known job ZIP used."""
        # 99999 -> DOWNTOWN_MONTGOMERY (32.3668, -86.3000)
        # 36117 -> (32.3700, -86.1800) -- east Montgomery, ~6mi from downtown
        result = estimate_commute(user_zip="99999", job_location="Montgomery, AL 36117")
        assert result.drive_min > 1
        # Should be too far to walk
        assert result.walk_min is None

    def test_job_location_without_zip(self):
        """Job location without ZIP -> falls back to downtown."""
        result = estimate_commute(user_zip="36104", job_location="Montgomery, AL")
        # 36104 is very close to downtown Montgomery
        assert result.drive_min >= 1
        assert result.drive_min <= 5


# ---------------------------------------------------------------------------
# Integration: wiring into ScoredJobMatch via pvs_scorer
# ---------------------------------------------------------------------------


class TestPvsScorerWiring:
    """Verify rank_all_jobs attaches commute_estimate to ScoredJobMatch."""

    def test_rank_all_jobs_attaches_commute_estimate(self):
        """ScoredJobMatch from rank_all_jobs should have commute_estimate."""
        from app.modules.matching.pvs_scorer import rank_all_jobs
        from app.modules.matching.types import AvailableHours, ScoringContext

        jobs = [
            {
                "title": "Cashier",
                "company": "Walmart",
                "location": "Montgomery, AL 36117",
                "description": "Part-time cashier position. $12/hr.",
            },
        ]
        ctx = ScoringContext(
            user_zip="36104",
            transit_dependent=False,
            schedule_type=AvailableHours.DAYTIME,
            barriers=[],
        )
        results = rank_all_jobs(jobs, ctx)
        assert len(results) == 1
        match = results[0]
        assert match.commute_estimate is not None
        assert match.commute_estimate.drive_min > 0

    def test_rank_all_jobs_commute_with_transit_info(self):
        """When job has transit_info, commute estimate should include transit."""
        from app.modules.matching.pvs_scorer import rank_all_jobs
        from app.modules.matching.types import AvailableHours, ScoringContext

        info = _make_transit_info(walk_miles=0.25)
        jobs = [
            {
                "title": "Cook",
                "company": "Diner",
                "location": "Montgomery, AL 36107",
                "description": "Line cook. $13/hr.",
                "transit_info": info,
            },
        ]
        ctx = ScoringContext(
            user_zip="36104",
            transit_dependent=True,
            schedule_type=AvailableHours.DAYTIME,
            barriers=[],
        )
        results = rank_all_jobs(jobs, ctx)
        assert len(results) == 1
        match = results[0]
        assert match.commute_estimate is not None
        assert match.commute_estimate.transit_min is not None

    def test_rank_all_jobs_commute_no_location(self):
        """Job without location -> commute estimate uses downtown fallback."""
        from app.modules.matching.pvs_scorer import rank_all_jobs
        from app.modules.matching.types import AvailableHours, ScoringContext

        jobs = [
            {
                "title": "Remote Worker",
                "company": "Tech Co",
                "description": "Remote position. $15/hr.",
            },
        ]
        ctx = ScoringContext(
            user_zip="36104",
            transit_dependent=False,
            schedule_type=AvailableHours.DAYTIME,
            barriers=[],
        )
        results = rank_all_jobs(jobs, ctx)
        assert len(results) == 1
        match = results[0]
        # Should still have commute estimate (fallback to downtown)
        assert match.commute_estimate is not None
        assert match.commute_estimate.drive_min >= 1

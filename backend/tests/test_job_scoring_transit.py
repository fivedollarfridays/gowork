"""Tests for job_scoring._score_transit with TransitInfo objects.

Covers the transit_info code path (lines 59-81) including:
- Walk distance scoring tiers
- Transfer count penalties
- Schedule feasibility multiplier
"""

import pytest

from app.modules.matching.job_scoring import _score_transit
from app.modules.matching.types_transit import RouteFeasibility, TransitInfo


def _route(walk_miles: float = 0.2, feasible: bool = True) -> RouteFeasibility:
    """Create a RouteFeasibility with sensible defaults."""
    return RouteFeasibility(
        route_number=1,
        route_name="Test Route",
        nearest_stop="Main & 1st",
        walk_miles=walk_miles,
        first_bus="05:00",
        last_bus="21:00",
        has_sunday=False,
        feasible=feasible,
    )


def _job_with_transit_info(
    transit_info: TransitInfo,
    transit_accessible: bool = True,
) -> dict:
    """Create a job dict with transit_info attached."""
    return {
        "title": "Test Job",
        "transit_accessible": transit_accessible,
        "transit_info": transit_info,
    }


class TestTransitInfoWalkDistance:
    """Walk distance factor scoring tiers."""

    def test_very_close_walk_scores_1(self):
        """Walk <= 0.25 miles scores 1.0."""
        info = TransitInfo(serving_routes=[_route(walk_miles=0.2)], transfer_count=0)
        job = _job_with_transit_info(info)
        score = _score_transit(job, transit_dependent=True)
        assert score == 1.0

    def test_short_walk_scores_0_9(self):
        """Walk 0.26-0.5 miles scores 0.9."""
        info = TransitInfo(serving_routes=[_route(walk_miles=0.4)], transfer_count=0)
        job = _job_with_transit_info(info)
        score = _score_transit(job, transit_dependent=True)
        assert score == 0.9

    def test_medium_walk_scores_0_7(self):
        """Walk 0.51-1.0 miles scores 0.7."""
        info = TransitInfo(serving_routes=[_route(walk_miles=0.8)], transfer_count=0)
        job = _job_with_transit_info(info)
        score = _score_transit(job, transit_dependent=True)
        assert score == 0.7

    def test_long_walk_scores_0_4(self):
        """Walk > 1.0 mile scores 0.4."""
        info = TransitInfo(serving_routes=[_route(walk_miles=1.5)], transfer_count=0)
        job = _job_with_transit_info(info)
        score = _score_transit(job, transit_dependent=True)
        assert score == 0.4

    def test_boundary_0_25_scores_1(self):
        """Walk exactly 0.25 miles scores 1.0."""
        info = TransitInfo(serving_routes=[_route(walk_miles=0.25)], transfer_count=0)
        job = _job_with_transit_info(info)
        assert _score_transit(job, transit_dependent=True) == 1.0

    def test_boundary_0_5_scores_0_9(self):
        """Walk exactly 0.5 miles scores 0.9."""
        info = TransitInfo(serving_routes=[_route(walk_miles=0.5)], transfer_count=0)
        job = _job_with_transit_info(info)
        assert _score_transit(job, transit_dependent=True) == 0.9

    def test_boundary_1_0_scores_0_7(self):
        """Walk exactly 1.0 mile scores 0.7."""
        info = TransitInfo(serving_routes=[_route(walk_miles=1.0)], transfer_count=0)
        job = _job_with_transit_info(info)
        assert _score_transit(job, transit_dependent=True) == 0.7


class TestTransitInfoTransferPenalty:
    """Transfer count penalty multiplier."""

    def test_zero_transfers_no_penalty(self):
        """No transfers: multiplier 1.0."""
        info = TransitInfo(serving_routes=[_route(walk_miles=0.2)], transfer_count=0)
        job = _job_with_transit_info(info)
        assert _score_transit(job, transit_dependent=True) == 1.0

    def test_one_transfer_0_8_penalty(self):
        """One transfer: multiplier 0.8."""
        info = TransitInfo(serving_routes=[_route(walk_miles=0.2)], transfer_count=1)
        job = _job_with_transit_info(info)
        assert _score_transit(job, transit_dependent=True) == 0.8

    def test_two_transfers_0_6_penalty(self):
        """Two+ transfers: multiplier 0.6."""
        info = TransitInfo(serving_routes=[_route(walk_miles=0.2)], transfer_count=2)
        job = _job_with_transit_info(info)
        assert _score_transit(job, transit_dependent=True) == 0.6

    def test_three_transfers_same_as_two(self):
        """Three transfers also uses 0.6 multiplier."""
        info = TransitInfo(serving_routes=[_route(walk_miles=0.2)], transfer_count=3)
        job = _job_with_transit_info(info)
        assert _score_transit(job, transit_dependent=True) == 0.6


class TestTransitInfoScheduleFeasibility:
    """Schedule feasibility multiplier on infeasible routes."""

    def test_all_feasible_no_penalty(self):
        """All routes feasible: schedule_mult 1.0."""
        info = TransitInfo(
            serving_routes=[_route(feasible=True), _route(feasible=True)],
            transfer_count=0,
        )
        job = _job_with_transit_info(info)
        assert _score_transit(job, transit_dependent=True) == 1.0

    def test_any_infeasible_halves_score(self):
        """Any infeasible route: schedule_mult 0.5."""
        info = TransitInfo(
            serving_routes=[_route(feasible=True), _route(feasible=False)],
            transfer_count=0,
        )
        job = _job_with_transit_info(info)
        assert _score_transit(job, transit_dependent=True) == 0.5


class TestTransitInfoCombined:
    """Combined walk + transfer + schedule scoring."""

    def test_medium_walk_one_transfer_infeasible(self):
        """0.8mi walk (0.7) * 1 transfer (0.8) * infeasible (0.5) = 0.280."""
        info = TransitInfo(
            serving_routes=[_route(walk_miles=0.8, feasible=False)],
            transfer_count=1,
        )
        job = _job_with_transit_info(info)
        score = _score_transit(job, transit_dependent=True)
        assert score == pytest.approx(0.28, abs=0.001)

    def test_empty_serving_routes_uses_fallback(self):
        """Empty serving_routes defaults walk to 1.0 -> score 0.7."""
        info = TransitInfo(serving_routes=[], transfer_count=0)
        job = _job_with_transit_info(info)
        score = _score_transit(job, transit_dependent=True)
        assert score == pytest.approx(0.7, abs=0.001)

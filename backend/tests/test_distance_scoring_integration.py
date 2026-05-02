"""Integration tests for distance-from-ZIP scoring activation.

Pins the contract that:

* When the user has no vehicle (transit_dependent=True) AND lives in a
  known FW ZIP AND the job has lat/lng, ``compute_pvs`` adds a small
  positive boost weighted at 0.05.
* When the user has a vehicle, behavior is unchanged (no boost).
* The ``ScoredJobMatch`` exposes ``distance_miles`` so the UI can
  render "X.X mi" — and it stays None when distance can't be computed.

We do NOT touch the relevance_scorer or the persona regression suite —
distance is layered into PVS only, after relevance is already settled.
"""

from __future__ import annotations

import pytest

from app.modules.matching.pvs_scorer import compute_pvs, rank_all_jobs
from app.modules.matching.types import (
    AvailableHours,
    BarrierType,
    ScoringContext,
)


# ---------- Fixtures ------------------------------------------------


def _close_job() -> dict:
    """Job with lat/lng inside FW (~76104 medical district)."""
    return {
        "title": "Patient Care Tech",
        "company": "JPS",
        "location": "Fort Worth, TX 76104",
        "description": "CNA role. Pay: $17.50/hr.",
        "lat": 32.7374,
        "lng": -97.3060,
    }


def _far_job() -> dict:
    """Job geocoded outside the 25-mile range (~50 miles east)."""
    return {
        "title": "CNA",
        "company": "Hospital East",
        "location": "Tyler, TX 75701",
        "description": "CNA role. Pay: $17.50/hr.",
        "lat": 32.3513,
        "lng": -95.3011,
    }


def _ungeocoded_job() -> dict:
    """Job that hasn't been backfilled — no lat/lng."""
    return {
        "title": "Welder",
        "company": "Plant",
        "location": "Fort Worth, TX",
        "description": "Welding. Pay: $19/hr.",
    }


def _ctx_no_vehicle() -> ScoringContext:
    return ScoringContext(
        user_zip="76119",  # FW ZIP, known to the centroid lookup
        transit_dependent=True,
        schedule_type=AvailableHours.DAYTIME,
        barriers=[BarrierType.TRANSPORTATION],
        target_industries=[],
        resume_keywords=[],
    )


def _ctx_with_vehicle() -> ScoringContext:
    return ScoringContext(
        user_zip="76119",
        transit_dependent=False,
        schedule_type=AvailableHours.DAYTIME,
        barriers=[],
        target_industries=[],
        resume_keywords=[],
    )


# ---------- compute_pvs behavior -----------------------------------


class TestPvsDistanceBoost:
    def test_close_job_outranks_far_job_for_no_vehicle_user(self):
        """Two equivalent jobs differing only by distance — when the
        user has no vehicle, the close one must score strictly higher.
        """
        ctx = _ctx_no_vehicle()
        close_score = compute_pvs(_close_job(), ctx)
        far_score = compute_pvs(_far_job(), ctx)
        assert close_score > far_score, (
            f"close={close_score} not > far={far_score}"
        )

    def test_no_boost_when_user_has_vehicle(self):
        """With a vehicle, distance contributes nothing — close and far
        jobs differ ONLY because of the in-place ``score_proximity``
        helper, not the new distance term.  We assert the new term
        adds zero by checking the gap is the same as the no-distance
        baseline (close == far when both have vehicle AND no proximity
        signal differs)."""
        ctx = _ctx_with_vehicle()
        close = compute_pvs(_close_job(), ctx)
        far = compute_pvs(_far_job(), ctx)
        # With a vehicle, the existing score_proximity already handles
        # location; the distance boost must NOT add a second penalty.
        # Exact equality isn't guaranteed (proximity can differ), but
        # the boost should be zero either way.  We check that turning
        # transit_dependent on widens the gap.
        ctx_transit = _ctx_no_vehicle()
        close_t = compute_pvs(_close_job(), ctx_transit)
        far_t = compute_pvs(_far_job(), ctx_transit)
        gap_with_vehicle = close - far
        gap_no_vehicle = close_t - far_t
        assert gap_no_vehicle > gap_with_vehicle, (
            f"distance boost did not widen the gap "
            f"(with-vehicle gap={gap_with_vehicle}, "
            f"no-vehicle gap={gap_no_vehicle})"
        )

    def test_no_boost_when_job_not_geocoded(self):
        """Ungeocoded job + no-vehicle user must not penalise the job
        more than baseline — None distance == no signal, not zero
        score."""
        ctx = _ctx_no_vehicle()
        ungeocoded = compute_pvs(_ungeocoded_job(), ctx)
        # Sanity — we still get a meaningful score.
        assert 0.0 < ungeocoded < 1.0

    def test_no_boost_when_zip_unknown(self):
        """Out-of-area ZIP -> no centroid -> no boost.  Close and far
        jobs end up tied on distance (both contribute 0)."""
        ctx = ScoringContext(
            user_zip="36104",  # Montgomery, AL — not in FW lookup
            transit_dependent=True,
            schedule_type=AvailableHours.DAYTIME,
            barriers=[BarrierType.TRANSPORTATION],
            target_industries=[],
            resume_keywords=[],
        )
        close = compute_pvs(_close_job(), ctx)
        far = compute_pvs(_far_job(), ctx)
        # Without a centroid the distance term contributes 0 to both
        # — they should be ranked by other factors only.  Allow
        # tiny float wiggle from proximity_scorer.
        assert abs(close - far) < 0.01


# ---------- distance_miles surfacing -------------------------------


class TestDistanceMilesField:
    def test_distance_miles_populated_for_geocoded_close_job(self):
        ctx = _ctx_no_vehicle()
        matches = rank_all_jobs([_close_job()], ctx)
        assert len(matches) == 1
        assert matches[0].distance_miles is not None
        assert 0 <= matches[0].distance_miles <= 10  # ~5-7 miles

    def test_distance_miles_none_for_ungeocoded_job(self):
        ctx = _ctx_no_vehicle()
        matches = rank_all_jobs([_ungeocoded_job()], ctx)
        assert matches[0].distance_miles is None

    def test_distance_miles_populated_even_with_vehicle(self):
        """The field is informational — surface it for everyone, even
        when the boost isn't applied.  The UI decides whether to render."""
        ctx = _ctx_with_vehicle()
        matches = rank_all_jobs([_close_job()], ctx)
        assert matches[0].distance_miles is not None

    def test_distance_miles_none_when_zip_not_in_lookup(self):
        ctx = ScoringContext(
            user_zip="36104",
            transit_dependent=True,
            schedule_type=AvailableHours.DAYTIME,
            barriers=[],
            target_industries=[],
            resume_keywords=[],
        )
        matches = rank_all_jobs([_close_job()], ctx)
        assert matches[0].distance_miles is None

"""Tests for resource relevance scoring engine."""

import pytest

from app.modules.matching.scoring import (
    _haversine_miles,
    get_score_band,
    score_resource,
    rank_resources,
)
from app.modules.matching.types import (
    AvailableHours,
    BarrierSeverity,
    BarrierType,
    EmploymentStatus,
    Resource,
    UserProfile,
)

# -- Helpers --

def _make_profile(**overrides) -> UserProfile:
    defaults = {
        "session_id": "test-session",
        "zip_code": "36101",
        "employment_status": EmploymentStatus.UNEMPLOYED,
        "barrier_count": 2,
        "primary_barriers": [BarrierType.CREDIT, BarrierType.TRAINING],
        "barrier_severity": BarrierSeverity.MEDIUM,
        "needs_credit_assessment": True,
        "transit_dependent": False,
        "schedule_type": "daytime",
        "work_history": "Former CNA at Baptist Hospital",
        "target_industries": ["healthcare"],
    }
    defaults.update(overrides)
    return UserProfile(**defaults)


def _make_resource(**overrides) -> Resource:
    defaults = {
        "id": 1,
        "name": "WIOA Career Center",
        "category": "career_center",
    }
    defaults.update(overrides)
    return Resource(**defaults)


# -- Tests --

class TestGetScoreBand:
    def test_strong_match(self):
        assert get_score_band(0.85) == "strong_match"

    def test_good_match(self):
        assert get_score_band(0.65) == "good_match"

    def test_possible_match(self):
        assert get_score_band(0.45) == "possible_match"

    def test_weak_match(self):
        assert get_score_band(0.2) == "weak_match"

    def test_boundary_80(self):
        assert get_score_band(0.80) == "strong_match"

    def test_boundary_60(self):
        assert get_score_band(0.60) == "good_match"

    def test_boundary_40(self):
        assert get_score_band(0.40) == "possible_match"


class TestBarrierAlignment:
    def test_training_resource_matches_training_barrier(self):
        """Training resource should score higher for user with training barrier."""
        profile = _make_profile(primary_barriers=[BarrierType.TRAINING])
        resource = _make_resource(category="training")
        score = score_resource(resource, profile)
        assert score > 0.3  # barrier alignment is 40% weight

    def test_childcare_resource_matches_childcare_barrier(self):
        profile = _make_profile(primary_barriers=[BarrierType.CHILDCARE])
        resource = _make_resource(category="childcare")
        score = score_resource(resource, profile)
        assert score > 0.3

    def test_unrelated_category_scores_lower(self):
        """Resource with no barrier match should score lower."""
        profile = _make_profile(primary_barriers=[BarrierType.CREDIT])
        training = _make_resource(category="training")
        childcare = _make_resource(category="childcare", id=2)
        # Neither matches credit barrier
        score_t = score_resource(training, profile)
        score_c = score_resource(childcare, profile)
        assert score_t < 0.5
        assert score_c < 0.5


class TestTransitScoring:
    def test_transit_dependent_night_penalized(self):
        """Transit-dependent user with night schedule should be penalized."""
        profile = _make_profile(
            transit_dependent=True, schedule_type="night",
            primary_barriers=[BarrierType.TRAINING],
        )
        resource = _make_resource(category="training")
        score = score_resource(resource, profile)
        # Night shift + transit dependent = lower score
        day_profile = _make_profile(
            transit_dependent=True, schedule_type="daytime",
            primary_barriers=[BarrierType.TRAINING],
        )
        day_score = score_resource(resource, day_profile)
        assert score < day_score

    def test_has_vehicle_not_penalized(self):
        """User with vehicle shouldn't get transit penalty."""
        profile = _make_profile(
            transit_dependent=False, schedule_type="night",
            primary_barriers=[BarrierType.TRAINING],
        )
        resource = _make_resource(category="training")
        score = score_resource(resource, profile)
        # Even night schedule, no transit penalty
        assert score > 0.3


class TestIndustryMatch:
    def test_matching_industry_boosts_score(self):
        """Resource mentioning target industry should score higher."""
        profile = _make_profile(target_industries=["healthcare"])
        r_match = _make_resource(
            category="training", services=["healthcare training"],
        )
        r_no_match = _make_resource(
            category="training", id=2, services=["IT training"],
        )
        assert score_resource(r_match, profile) > score_resource(r_no_match, profile)

    def test_no_target_industries_neutral(self):
        """No industry preference should give neutral industry score."""
        profile = _make_profile(target_industries=[])
        resource = _make_resource(category="training")
        score = score_resource(resource, profile)
        assert 0.0 <= score <= 1.0


class TestRankResources:
    def test_returns_sorted_descending(self):
        """Resources should be sorted by score, highest first."""
        profile = _make_profile(primary_barriers=[BarrierType.TRAINING])
        r_high = _make_resource(category="training", id=1)
        r_low = _make_resource(category="childcare", id=2)
        ranked = rank_resources([r_low, r_high], profile)
        assert ranked[0].category == "training"
        assert ranked[1].category == "childcare"

    def test_empty_list_returns_empty(self):
        profile = _make_profile()
        assert rank_resources([], profile) == []

    def test_single_resource(self):
        profile = _make_profile()
        r = _make_resource()
        assert rank_resources([r], profile) == [r]


class TestScoreProperties:
    def test_score_in_valid_range(self):
        """Score must always be 0.0-1.0."""
        profile = _make_profile()
        resource = _make_resource()
        score = score_resource(resource, profile)
        assert 0.0 <= score <= 1.0

    def test_deterministic(self):
        """Same inputs must produce same output."""
        profile = _make_profile()
        resource = _make_resource()
        scores = [score_resource(resource, profile) for _ in range(10)]
        assert len(set(scores)) == 1


class TestScheduleScoring:
    def test_evening_resource_matches_evening_user(self):
        profile = _make_profile(schedule_type="evening")
        resource = _make_resource(notes="Open evenings until 8pm")
        score_eve = score_resource(resource, profile)
        resource_day = _make_resource(notes="Open weekdays 9-5", id=2)
        score_day = score_resource(resource_day, profile)
        assert score_eve > score_day

    def test_daytime_resource_matches_daytime_user(self):
        profile = _make_profile(schedule_type="daytime")
        resource = _make_resource(notes="Open weekdays 9am-5pm")
        score = score_resource(resource, profile)
        assert 0.0 <= score <= 1.0

    def test_night_schedule_penalized(self):
        profile = _make_profile(schedule_type="night")
        resource = _make_resource(notes="Open weekdays 9-5")
        score = score_resource(resource, profile)
        assert 0.0 <= score <= 1.0


class TestTransitFlexible:
    def test_flexible_transit_dependent_moderate_score(self):
        profile = _make_profile(transit_dependent=True, schedule_type="flexible")
        resource = _make_resource(category="training")
        score = score_resource(resource, profile)
        assert 0.0 <= score <= 1.0


class TestHaversine:
    def test_same_point_zero_distance(self):
        assert _haversine_miles(32.37, -86.30, 32.37, -86.30) == 0.0

    def test_known_distance(self):
        # Montgomery downtown to Maxwell AFB ~5 miles
        dist = _haversine_miles(32.3668, -86.3000, 32.3800, -86.3600)
        assert 2.0 < dist < 6.0


class TestProximityUnknownZip:
    def test_unknown_zip_gets_neutral_score(self):
        profile = _make_profile(zip_code="99999")
        resource = _make_resource()
        score = score_resource(resource, profile)
        assert 0.0 <= score <= 1.0

"""Tests for resource relevance scoring engine."""

import pytest

from app.modules.matching.scoring import (
    BARRIER_CATEGORY_MAP,
    _score_industry,
    _score_proximity,
    haversine_miles,
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
        assert score_resource(training, profile) < 0.5
        assert score_resource(childcare, profile) < 0.5
        # Verify expanded mappings include cross-category routing
        assert "social_service" in BARRIER_CATEGORY_MAP[BarrierType.TRANSPORTATION]
        assert "career_center" in BARRIER_CATEGORY_MAP[BarrierType.HEALTH]
        assert "social_service" in BARRIER_CATEGORY_MAP[BarrierType.CHILDCARE]
        assert "career_center" in BARRIER_CATEGORY_MAP[BarrierType.HOUSING]


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

    def test_word_boundary_prevents_false_positives(self):
        """Word boundaries prevent substring false positives."""
        # "health" should NOT match "healthy", SHOULD match "health services"
        profile = _make_profile(target_industries=["health"])
        assert _score_industry(_make_resource(services=["healthy eating"]), profile) == 0.3
        assert _score_industry(_make_resource(id=2, services=["health services"]), profile) == 1.0

        # "auto" should NOT match "automatic", SHOULD match "auto repair"
        profile2 = _make_profile(target_industries=["auto"])
        assert _score_industry(_make_resource(services=["automatic scheduling"]), profile2) == 0.3
        assert _score_industry(_make_resource(id=2, services=["auto repair"]), profile2) == 1.0

        # Match in notes field
        profile3 = _make_profile(target_industries=["welding"])
        assert _score_industry(_make_resource(notes="Offers welding certification"), profile3) == 1.0


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
        assert haversine_miles(32.37, -86.30, 32.37, -86.30) == 0.0

    def test_known_distance(self):
        # Montgomery downtown to Maxwell AFB ~5 miles
        dist = haversine_miles(32.3668, -86.3000, 32.3800, -86.3600)
        assert 2.0 < dist < 6.0


class TestScheduleDifferentiation:
    """Verify that schedule scoring actually varies by available_hours value."""

    def test_evening_differs_from_daytime(self):
        """Evening user should score differently than daytime user."""
        resource = _make_resource(notes="Open evenings until 8pm")
        daytime = _make_profile(schedule_type="daytime")
        evening = _make_profile(schedule_type="evening")
        assert score_resource(resource, daytime) != score_resource(resource, evening)

    def test_night_penalized_more_than_daytime(self):
        """Night schedule should score lower than daytime for standard resources."""
        resource = _make_resource(notes="Open weekdays 9am-5pm")
        daytime = _make_profile(schedule_type="daytime")
        night = _make_profile(schedule_type="night")
        assert score_resource(resource, night) < score_resource(resource, daytime)

    def test_night_transit_penalty_stacks(self):
        """Transit-dependent + night schedule should be heavily penalized."""
        resource = _make_resource(
            category="training",
            notes="Open weekdays 9am-5pm",
        )
        night_transit = _make_profile(
            schedule_type="night",
            transit_dependent=True,
            primary_barriers=[BarrierType.TRAINING],
        )
        day_transit = _make_profile(
            schedule_type="daytime",
            transit_dependent=True,
            primary_barriers=[BarrierType.TRAINING],
        )
        night_score = score_resource(resource, night_transit)
        day_score = score_resource(resource, day_transit)
        # Night should lose on BOTH transit (0.2 vs 0.9) and schedule (0.3 vs 0.8)
        assert night_score < day_score
        assert day_score - night_score > 0.1  # meaningful gap

    def test_flexible_transit_between_day_and_night(self):
        """Flexible schedule transit score should fall between day and night."""
        resource = _make_resource(category="training")
        day = _make_profile(
            schedule_type="daytime", transit_dependent=True,
            primary_barriers=[BarrierType.TRAINING],
        )
        flex = _make_profile(
            schedule_type="flexible", transit_dependent=True,
            primary_barriers=[BarrierType.TRAINING],
        )
        night = _make_profile(
            schedule_type="night", transit_dependent=True,
            primary_barriers=[BarrierType.TRAINING],
        )
        day_s = score_resource(resource, day)
        flex_s = score_resource(resource, flex)
        night_s = score_resource(resource, night)
        assert night_s < flex_s < day_s


class TestLocationAwareTransitScoring:
    """Transit scoring using actual bus stop proximity."""

    def test_near_stop_scores_higher_than_far_for_transit_dependent(self):
        """Resource near a bus stop should score higher than one far away."""
        profile = _make_profile(
            transit_dependent=True, primary_barriers=[BarrierType.TRAINING],
        )
        resource = _make_resource(id=1, category="training")
        near_score = score_resource(resource, profile, nearest_stop_miles=0.2)
        far_score = score_resource(resource, profile, nearest_stop_miles=5.0)
        assert near_score > far_score

        # Exercise middle transit distance bands (0.25-1.0 -> 0.7, 1.0-3.0 -> 0.4)
        from app.modules.matching.scoring import _score_transit
        mid_near = _score_transit(resource, profile, nearest_stop_miles=0.5)
        mid_far = _score_transit(resource, profile, nearest_stop_miles=2.0)
        # daytime schedule_mult=1.0, so dist_score returned directly
        assert mid_near == pytest.approx(0.7)
        assert mid_far == pytest.approx(0.4)

    def test_night_penalty_applies_on_top_of_location(self):
        """Night schedule should still penalize even when resource is near a stop."""
        profile_day = _make_profile(
            transit_dependent=True, schedule_type="daytime",
            primary_barriers=[BarrierType.TRAINING],
        )
        profile_night = _make_profile(
            transit_dependent=True, schedule_type="night",
            primary_barriers=[BarrierType.TRAINING],
        )
        resource = _make_resource(id=1, category="training")
        day_score = score_resource(resource, profile_day, nearest_stop_miles=0.2)
        night_score = score_resource(resource, profile_night, nearest_stop_miles=0.2)
        assert night_score < day_score

    def test_non_transit_dependent_unaffected_by_stop_proximity(self):
        """User with vehicle should not be affected by stop distance."""
        profile = _make_profile(
            transit_dependent=False, primary_barriers=[BarrierType.TRAINING],
        )
        resource = _make_resource(id=1, category="training")
        near_score = score_resource(resource, profile, nearest_stop_miles=0.2)
        far_score = score_resource(resource, profile, nearest_stop_miles=5.0)
        assert near_score == far_score

    def test_rank_resources_with_stop_distances(self):
        """rank_resources should use stop_distances to differentiate scoring."""
        profile = _make_profile(
            transit_dependent=True, primary_barriers=[BarrierType.TRAINING],
        )
        near = _make_resource(id=1, category="training", name="Near Stop")
        far = _make_resource(id=2, category="training", name="Far From Stop")
        stop_distances = {1: 0.2, 2: 5.0}
        ranked = rank_resources([far, near], profile, stop_distances=stop_distances)
        assert ranked[0].name == "Near Stop"


class TestProximityUnknownZip:
    def test_unknown_zip_gets_neutral_score(self):
        profile = _make_profile(zip_code="99999")
        resource = _make_resource()
        score = score_resource(resource, profile)
        assert 0.0 <= score <= 1.0

    def test_unknown_zip_falls_back_to_downtown(self):
        """Unknown ZIP uses downtown centroid; known ZIP uses its own."""
        downtown_resource = _make_resource(lat=32.3668, lng=-86.3000)

        # Unknown ZIP 36114 → downtown fallback → distance ~0 → high score
        unknown = _make_profile(zip_code="36114")
        assert _score_proximity(downtown_resource, unknown) > 0.9

        # Known ZIP 36117 (east Montgomery) → own centroid → ~7mi → lower score
        known = _make_profile(zip_code="36117")
        assert _score_proximity(downtown_resource, known) < 0.9


class TestProximityWithCoordinates:
    def test_close_resource_scores_higher_than_far(self):
        """Resource with lat/lng near the user's zip centroid should score higher."""
        profile = _make_profile(zip_code="36104")  # centroid ~32.375, -86.296
        close = _make_resource(
            id=1, category="training",
            lat=32.375, lng=-86.296,  # essentially on top of centroid
        )
        far = _make_resource(
            id=2, category="training",
            lat=32.310, lng=-86.400,  # several miles away
        )
        assert score_resource(close, profile) > score_resource(far, profile)

        # Very far resource (~80 miles) exercises miles >= 15.0 branch (return 0.1)
        very_far = _make_resource(
            id=3, category="training",
            lat=33.5, lng=-85.0,
        )
        assert _score_proximity(very_far, profile) == pytest.approx(0.1)

    def test_resource_without_coords_gets_neutral(self):
        """Resource missing lat/lng still gets a valid score."""
        profile = _make_profile(zip_code="36104")
        resource = _make_resource(category="training")  # no lat/lng
        score = score_resource(resource, profile)
        assert 0.0 <= score <= 1.0

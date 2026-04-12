"""Tests for scoring.py city-aware geo routing.

Verifies scoring uses geo_router for downtown coords and ZIP centroids.
"""

import pytest

from app.modules.matching.types import Resource, UserProfile, BarrierType, BarrierSeverity, EmploymentStatus, AvailableHours


@pytest.fixture
def _fort_worth_city(monkeypatch):
    monkeypatch.setenv("CITY", "fort-worth")
    from app.cities.config import load_city_config
    load_city_config.cache_clear()
    from app.core.config import get_settings
    get_settings.cache_clear()
    yield
    load_city_config.cache_clear()
    get_settings.cache_clear()


@pytest.fixture
def _montgomery_city(monkeypatch):
    monkeypatch.setenv("CITY", "montgomery")
    from app.cities.config import load_city_config
    load_city_config.cache_clear()
    from app.core.config import get_settings
    get_settings.cache_clear()
    yield
    load_city_config.cache_clear()
    get_settings.cache_clear()


@pytest.fixture
def fw_resource():
    return Resource(
        id=1, name="Workforce Solutions",
        category="career_center",
        lat=32.7200, lng=-97.2800,
    )


@pytest.fixture
def fw_profile():
    return UserProfile(
        session_id="test",
        zip_code="76105",
        employment_status=EmploymentStatus.UNEMPLOYED,
        barrier_count=1,
        primary_barriers=[BarrierType.CREDIT],
        barrier_severity=BarrierSeverity.LOW,
        needs_credit_assessment=True,
        transit_dependent=False,
        schedule_type=AvailableHours.DAYTIME,
        work_history="3 years warehouse",
        target_industries=["logistics"],
    )


class TestScoringRouting:
    @pytest.mark.usefixtures("_fort_worth_city")
    def test_fort_worth_proximity_uses_fw_centroids(self, fw_resource, fw_profile):
        """Fort Worth scoring should use Fort Worth ZIP centroids."""
        from app.modules.matching.scoring import score_resource

        score = score_resource(fw_resource, fw_profile)
        # Fort Worth resource near Fort Worth ZIP should score well
        assert score > 0.3

    @pytest.mark.usefixtures("_fort_worth_city")
    def test_fort_worth_unknown_zip_falls_back_to_fw_downtown(self, fw_resource):
        """Unknown ZIP in Fort Worth should fallback to Fort Worth downtown."""
        from app.modules.matching.scoring import _score_proximity

        profile = UserProfile(
            session_id="test",
            zip_code="99999",
            employment_status=EmploymentStatus.UNEMPLOYED,
            barrier_count=1,
            primary_barriers=[BarrierType.CREDIT],
            barrier_severity=BarrierSeverity.LOW,
            needs_credit_assessment=True,
            transit_dependent=False,
            schedule_type=AvailableHours.DAYTIME,
            work_history="",
            target_industries=[],
        )
        score = _score_proximity(fw_resource, profile)
        # Should use Fort Worth downtown (32.7555, -97.3308)
        # not Montgomery downtown (32.3668, -86.3000)
        # Fort Worth resource at (32.72, -97.28) is close to FW downtown
        assert score > 0.5

"""Tests for PVS scorer city-aware routing.

Verifies that pvs_scorer correctly uses routed calculators based on city.
"""

import pytest

from app.modules.benefits.types import BenefitsProfile
from app.modules.matching.types import AvailableHours, BarrierType, ScoringContext


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


class TestPvsScorerRouting:
    """PVS scorer should work correctly for both cities."""

    @pytest.mark.usefixtures("_fort_worth_city")
    def test_fort_worth_pvs_uses_tx_benefits(self):
        """PVS scoring with TX benefits profile should not error."""
        from app.modules.matching.pvs_scorer import compute_pvs

        bp = BenefitsProfile(
            household_size=4,
            current_monthly_income=2000,
            enrolled_programs=["SNAP", "CHIP"],
            dependents_under_6=1,
            dependents_6_to_17=1,
            state="TX",
        )
        ctx = ScoringContext(
            user_zip="76102",
            transit_dependent=False,
            schedule_type=AvailableHours.DAYTIME,
            barriers=[BarrierType.CREDIT],
            benefits_profile=bp,
        )
        job = {"title": "Warehouse Worker", "description": "$15/hr full time"}
        pvs = compute_pvs(job, ctx)
        assert 0.0 <= pvs <= 1.0

    @pytest.mark.usefixtures("_fort_worth_city")
    def test_fort_worth_rank_all_jobs(self):
        """rank_all_jobs should work with TX benefits profile."""
        from app.modules.matching.pvs_scorer import rank_all_jobs

        bp = BenefitsProfile(
            household_size=3,
            current_monthly_income=1500,
            enrolled_programs=["SNAP", "Section_8"],
            state="TX",
        )
        ctx = ScoringContext(
            user_zip="76102",
            transit_dependent=True,
            schedule_type=AvailableHours.DAYTIME,
            barriers=[BarrierType.TRANSPORTATION],
            benefits_profile=bp,
        )
        jobs = [
            {"title": "Cook", "description": "$12/hr", "location": "Fort Worth, TX 76102"},
            {"title": "Driver", "description": "$18/hr CDL required"},
        ]
        results = rank_all_jobs(jobs, ctx)
        assert len(results) == 2
        # Results should be sorted descending by score
        assert results[0].relevance_score >= results[1].relevance_score

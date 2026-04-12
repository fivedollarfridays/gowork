"""Tests for city-aware pathway generation.

These tests override the autouse _set_city_for_pathway_tests fixture
from conftest by explicitly setting CITY via monkeypatch and clearing
caches within each test body.
"""

import pytest

from app.cities.config import load_city_config
from app.core.config import get_settings
from app.modules.benefits.types import BenefitsProfile
from app.modules.pathway.types import PathwayResult


class TestMontgomeryPathways:
    """Pathways should work for CITY=montgomery (Alabama)."""

    def test_montgomery_snap_pathway(self, monkeypatch):
        monkeypatch.setenv("CITY", "montgomery")
        get_settings.cache_clear()
        load_city_config.cache_clear()

        from app.modules.pathway.engine import generate_pathways

        profile = BenefitsProfile(
            household_size=3,
            current_monthly_income=1200.0,
            enrolled_programs=["SNAP"],
            dependents_under_6=1,
            dependents_6_to_17=0,
            state="AL",
        )
        result = generate_pathways(
            barrier_ids=["criminal_record"],
            benefits_profile=profile,
            current_wage=0.0,
        )
        assert isinstance(result, PathwayResult)
        assert len(result.pathways) >= 1
        assert result.best_pathway is not None

    def test_montgomery_all_kids_program(self, monkeypatch):
        monkeypatch.setenv("CITY", "montgomery")
        get_settings.cache_clear()
        load_city_config.cache_clear()

        from app.modules.pathway.engine import generate_pathways

        profile = BenefitsProfile(
            household_size=4,
            current_monthly_income=1500.0,
            enrolled_programs=["SNAP", "ALL_Kids"],
            dependents_under_6=1,
            dependents_6_to_17=1,
            state="AL",
        )
        result = generate_pathways(
            barrier_ids=["credit", "transportation"],
            benefits_profile=profile,
            current_wage=8.0,
        )
        assert len(result.pathways) == 3


class TestFortWorthPathways:
    """Pathways should work for CITY=fort-worth (Texas)."""

    def test_fort_worth_chip_pathway(self):
        """Uses autouse fixture which already sets CITY=fort-worth."""
        from app.modules.pathway.engine import generate_pathways

        profile = BenefitsProfile(
            household_size=3,
            current_monthly_income=1200.0,
            enrolled_programs=["SNAP", "CHIP"],
            dependents_under_6=1,
            dependents_6_to_17=0,
            state="TX",
        )
        result = generate_pathways(
            barrier_ids=["criminal_record", "childcare"],
            benefits_profile=profile,
            current_wage=0.0,
        )
        assert len(result.pathways) >= 1
        best = result.best_pathway
        assert best is not None
        assert best.final_net_monthly > 0


class TestEdgeCases:
    """Edge cases for pathway generation."""

    def test_max_barriers(self):
        from app.modules.pathway.engine import generate_pathways

        all_barriers = [
            "criminal_record", "credit", "transportation",
            "childcare", "housing", "health", "training",
        ]
        profile = BenefitsProfile(
            household_size=4,
            current_monthly_income=800.0,
            enrolled_programs=["SNAP", "CHIP", "Childcare_Subsidy"],
            dependents_under_6=2,
            dependents_6_to_17=0,
            state="TX",
        )
        result = generate_pathways(
            barrier_ids=all_barriers,
            benefits_profile=profile,
            current_wage=0.0,
        )
        assert len(result.pathways) >= 1
        assert set(result.barriers_active) == set(all_barriers)
        assert result.best_pathway.viability_score < 0.8

    def test_high_current_wage(self):
        from app.modules.pathway.engine import generate_pathways

        profile = BenefitsProfile(
            household_size=1,
            current_monthly_income=3000.0,
            enrolled_programs=[],
            state="TX",
        )
        result = generate_pathways(
            barrier_ids=["training"],
            benefits_profile=profile,
            current_wage=20.0,
        )
        assert len(result.pathways) >= 1
        assert result.current_wage == 20.0

    def test_empty_everything(self):
        from app.modules.pathway.engine import generate_pathways

        profile = BenefitsProfile()
        result = generate_pathways(
            barrier_ids=[],
            benefits_profile=profile,
            current_wage=0.0,
        )
        assert len(result.pathways) >= 1
        assert result.current_wage == 0.0

"""Tests for resource eligibility engine."""

import pytest

from app.modules.benefits.types import BenefitsProfile
from app.modules.matching.types import Resource
from app.modules.resources.eligibility import (
    ELIGIBILITY_RULES,
    EligibilityStatus,
    check_eligibility,
)


def _resource(name: str = "Test Resource", **kw) -> Resource:
    defaults = {
        "id": 1, "name": name, "category": "social_service",
        "subcategory": None, "address": None, "phone": None,
        "url": None, "eligibility": None, "services": None,
        "notes": None,
    }
    defaults.update(kw)
    return Resource(**defaults)


def _profile(**kw) -> BenefitsProfile:
    defaults = {
        "household_size": 3,
        "current_monthly_income": 1500.0,
        "enrolled_programs": [],
        "dependents_under_6": 1,
        "dependents_6_to_17": 0,
    }
    defaults.update(kw)
    return BenefitsProfile(**defaults)


class TestEligibilityStatus:
    """Verify enum values."""

    def test_has_likely(self) -> None:
        assert EligibilityStatus.LIKELY == "likely"

    def test_has_check(self) -> None:
        assert EligibilityStatus.CHECK == "check"

    def test_has_unknown(self) -> None:
        assert EligibilityStatus.UNKNOWN == "unknown"


class TestNoProfile:
    """Without a BenefitsProfile, everything is unknown."""

    def test_no_profile_returns_unknown(self) -> None:
        r = _resource("Alabama DHR Child Care Subsidy Program")
        assert check_eligibility(r, None) == EligibilityStatus.UNKNOWN

    def test_unknown_resource_returns_unknown(self) -> None:
        r = _resource("Some Random Org")
        assert check_eligibility(r, _profile()) == EligibilityStatus.UNKNOWN


class TestIncomeBasedEligibility:
    """Resources with income thresholds (FPL-based)."""

    def test_head_start_low_income_likely(self) -> None:
        """Family at poverty level with young kids → likely eligible."""
        r = _resource("Head Start / Early Head Start, Montgomery")
        profile = _profile(
            household_size=3,
            current_monthly_income=1500.0,  # ~$18k/yr, below 100% FPL ($26,700)
            dependents_under_6=1,
        )
        assert check_eligibility(r, profile) == EligibilityStatus.LIKELY

    def test_head_start_high_income_check(self) -> None:
        """Family above FPL → check eligibility."""
        r = _resource("Head Start / Early Head Start, Montgomery")
        profile = _profile(
            household_size=3,
            current_monthly_income=3000.0,  # ~$36k/yr, above 100% FPL
            dependents_under_6=1,
        )
        assert check_eligibility(r, profile) == EligibilityStatus.CHECK

    def test_head_start_no_young_kids_check(self) -> None:
        """No dependents under 6 → check (may not qualify)."""
        r = _resource("Head Start / Early Head Start, Montgomery")
        profile = _profile(dependents_under_6=0, dependents_6_to_17=1)
        assert check_eligibility(r, profile) == EligibilityStatus.CHECK


class TestProgramEnrollment:
    """Resources requiring specific program enrollment."""

    def test_jobs_program_tanf_enrolled_likely(self) -> None:
        """TANF recipient → likely eligible for JOBS program."""
        r = _resource("Alabama JOBS Program (DHR)")
        profile = _profile(enrolled_programs=["TANF"])
        assert check_eligibility(r, profile) == EligibilityStatus.LIKELY

    def test_jobs_program_no_tanf_check(self) -> None:
        """Not on TANF → check eligibility."""
        r = _resource("Alabama JOBS Program (DHR)")
        profile = _profile(enrolled_programs=["SNAP"])
        assert check_eligibility(r, profile) == EligibilityStatus.CHECK


class TestChildcareSubsidy:
    """DHR Childcare subsidy — income + dependents."""

    def test_low_income_with_kids_likely(self) -> None:
        r = _resource("Alabama DHR Child Care Subsidy Program")
        profile = _profile(
            household_size=3,
            current_monthly_income=1500.0,
            dependents_under_6=1,
        )
        assert check_eligibility(r, profile) == EligibilityStatus.LIKELY

    def test_high_income_check(self) -> None:
        r = _resource("Alabama DHR Child Care Subsidy Program")
        profile = _profile(
            household_size=3,
            current_monthly_income=4500.0,  # ~$54k/yr, above 85% SMI
            dependents_under_6=1,
        )
        assert check_eligibility(r, profile) == EligibilityStatus.CHECK

    def test_no_kids_check(self) -> None:
        r = _resource("Alabama DHR Child Care Subsidy Program")
        profile = _profile(dependents_under_6=0, dependents_6_to_17=0)
        assert check_eligibility(r, profile) == EligibilityStatus.CHECK


class TestOpenToAll:
    """Resources open to everyone → always likely."""

    def test_career_center_always_likely(self) -> None:
        r = _resource("Montgomery Career Center (Comprehensive)")
        assert check_eligibility(r, _profile()) == EligibilityStatus.LIKELY

    def test_greenpath_always_likely(self) -> None:
        r = _resource("GreenPath Financial Wellness")
        assert check_eligibility(r, _profile()) == EligibilityStatus.LIKELY

    def test_trenholm_always_likely(self) -> None:
        r = _resource("Trenholm State Community College")
        assert check_eligibility(r, _profile()) == EligibilityStatus.LIKELY

    def test_food_bank_always_likely(self) -> None:
        r = _resource("Montgomery Area Food Bank")
        assert check_eligibility(r, _profile()) == EligibilityStatus.LIKELY


class TestCriminalRecordResources:
    """MPACT is specifically for returning citizens."""

    def test_mpact_always_likely(self) -> None:
        r = _resource("MPACT, Montgomery Preparedness and Career Training")
        assert check_eligibility(r, _profile()) == EligibilityStatus.LIKELY


class TestRulesCompleteness:
    """Verify rules cover our seed resources."""

    def test_rules_dict_is_not_empty(self) -> None:
        assert len(ELIGIBILITY_RULES) > 0

    def test_all_rules_have_valid_type(self) -> None:
        for name, rule in ELIGIBILITY_RULES.items():
            assert "type" in rule, f"Rule '{name}' missing 'type'"
            assert rule["type"] in ("open", "income", "enrollment", "compound")

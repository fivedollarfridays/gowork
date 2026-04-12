"""Tests for Texas benefits eligibility checks."""

import pytest

from app.modules.benefits.types import BenefitsProfile, EligibilityConfidence


def _profile(**kwargs) -> BenefitsProfile:
    defaults = {
        "household_size": 3,
        "current_monthly_income": 1500.0,
        "enrolled_programs": [],
        "dependents_under_6": 1,
        "dependents_6_to_17": 0,
        "state": "TX",
    }
    defaults.update(kwargs)
    return BenefitsProfile(**defaults)


class TestTexasSNAP:
    def test_eligible_below_130_fpl(self):
        from app.modules.benefits.texas.eligibility_checks import PROGRAM_CHECKS

        result = PROGRAM_CHECKS["SNAP"](18000, 3, 1, _profile())
        assert result.eligible
        assert result.program == "SNAP"

    def test_ineligible_above_130_fpl(self):
        from app.modules.benefits.texas.eligibility_checks import PROGRAM_CHECKS

        result = PROGRAM_CHECKS["SNAP"](50000, 3, 1, _profile())
        assert not result.eligible


class TestTexasTANF:
    def test_eligible_below_limit(self):
        from app.modules.benefits.texas.eligibility_checks import PROGRAM_CHECKS

        result = PROGRAM_CHECKS["TANF"](2000, 3, 1, _profile())
        assert result.eligible

    def test_tanf_higher_than_alabama(self):
        """TX TANF max benefit for size 3 is $308, higher than AL's $215."""
        from app.modules.benefits.texas.eligibility_checks import PROGRAM_CHECKS

        result = PROGRAM_CHECKS["TANF"](1000, 3, 1, _profile())
        assert result.estimated_monthly_value >= 308


class TestTexasMedicaid:
    def test_not_expanded(self):
        """Texas has not expanded Medicaid for adults."""
        from app.modules.benefits.texas.eligibility_checks import PROGRAM_CHECKS

        result = PROGRAM_CHECKS["Medicaid"](15000, 1, 0, _profile(household_size=1))
        assert not result.eligible
        assert "Texas" in result.reason


class TestTexasCHIP:
    def test_eligible_with_children(self):
        from app.modules.benefits.texas.eligibility_checks import PROGRAM_CHECKS

        result = PROGRAM_CHECKS["CHIP"](30000, 3, 1, _profile())
        assert result.eligible
        assert result.program == "CHIP"

    def test_ineligible_no_children(self):
        from app.modules.benefits.texas.eligibility_checks import PROGRAM_CHECKS

        p = _profile(dependents_under_6=0, dependents_6_to_17=0)
        result = PROGRAM_CHECKS["CHIP"](20000, 3, 0, p)
        assert not result.eligible

    def test_threshold_at_200_fpl(self):
        """CHIP threshold is 200% FPL (lower than AL ALL_Kids at 317%)."""
        from app.modules.benefits.texas.eligibility_checks import PROGRAM_CHECKS
        from app.modules.benefits.texas.thresholds import FPL_2026

        fpl_3 = FPL_2026[3]
        # Just under 200% FPL
        result = PROGRAM_CHECKS["CHIP"](fpl_3 * 1.99, 3, 1, _profile())
        assert result.eligible
        # Just over 200% FPL
        result = PROGRAM_CHECKS["CHIP"](fpl_3 * 2.01, 3, 1, _profile())
        assert not result.eligible


class TestTexasCEAP:
    def test_eligible_below_150_fpl(self):
        from app.modules.benefits.texas.eligibility_checks import PROGRAM_CHECKS

        result = PROGRAM_CHECKS["CEAP"](15000, 1, 0, _profile(household_size=1))
        assert result.eligible
        assert result.program == "CEAP"

    def test_ineligible_above_150_fpl(self):
        from app.modules.benefits.texas.eligibility_checks import PROGRAM_CHECKS

        result = PROGRAM_CHECKS["CEAP"](50000, 1, 0, _profile(household_size=1))
        assert not result.eligible


class TestTexasSection8:
    def test_uses_fort_worth_ami(self):
        """Section 8 should use Fort Worth AMI, not Montgomery AMI."""
        from app.modules.benefits.texas.eligibility_checks import PROGRAM_CHECKS
        from app.modules.benefits.texas.thresholds import AMI_FORT_WORTH_2026

        ami_3 = AMI_FORT_WORTH_2026[3]
        # Just under 50% AMI
        result = PROGRAM_CHECKS["Section_8"](ami_3 * 0.49, 3, 0, _profile())
        assert result.eligible
        # Just over 50% AMI
        result = PROGRAM_CHECKS["Section_8"](ami_3 * 0.51, 3, 0, _profile())
        assert not result.eligible


class TestAllProgramsExist:
    def test_seven_programs_in_checks(self):
        from app.modules.benefits.texas.eligibility_checks import PROGRAM_CHECKS

        expected = {"SNAP", "TANF", "Medicaid", "CHIP", "Childcare_Subsidy", "Section_8", "CEAP"}
        assert set(PROGRAM_CHECKS.keys()) == expected

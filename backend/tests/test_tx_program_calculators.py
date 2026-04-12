"""Tests for Texas program calculators to push coverage.

Targets uncovered lines in texas/program_calculators.py:
- Lines 41-46: calc_tanf returns max_benefit when below income limit
- Line 51: calc_medicaid returns 0.0 (TX no expansion)
- Line 60: calc_chip returns 0.0 when no children or over FPL
- Lines 67, 71: calc_childcare no dependents_under_6 and over SMI limit
"""

import pytest

from app.modules.benefits.types import BenefitsProfile
from app.modules.benefits.texas.program_calculators import (
    calc_ceap,
    calc_chip,
    calc_childcare,
    calc_medicaid,
    calc_section_8,
    calc_snap,
    calc_tanf,
    sum_program_benefits,
)


class TestCalcTanf:
    """TX TANF calculator edge cases."""

    def test_below_income_limit_returns_max(self):
        """Low income should return max TANF benefit."""
        profile = BenefitsProfile(
            household_size=3, current_monthly_income=200,
            enrolled_programs=["TANF"], state="TX",
        )
        # TX TANF limit for hs=3: $308 * 12 * 0.75 = $2772, use $2000
        result = calc_tanf(2000.0, profile)
        assert result > 0

    def test_above_income_limit_returns_zero(self):
        """High income should return zero."""
        profile = BenefitsProfile(
            household_size=3, current_monthly_income=5000,
            enrolled_programs=["TANF"], state="TX",
        )
        result = calc_tanf(80000.0, profile)
        assert result == 0.0

    def test_at_exact_limit(self):
        """At the exact income limit boundary."""
        from app.modules.benefits.texas.thresholds import TANF_MAX_MONTHLY, MONTHS_PER_YEAR

        hs = 3
        max_benefit = TANF_MAX_MONTHLY.get(hs, 308)
        limit = max_benefit * MONTHS_PER_YEAR * 0.75
        profile = BenefitsProfile(
            household_size=hs, current_monthly_income=1000,
            enrolled_programs=["TANF"], state="TX",
        )
        # Just below limit
        result_below = calc_tanf(limit - 1, profile)
        assert result_below == max_benefit
        # Just above limit
        result_above = calc_tanf(limit + 1, profile)
        assert result_above == 0.0


class TestCalcMedicaid:
    """TX Medicaid: no expansion, always $0."""

    def test_always_returns_zero(self):
        profile = BenefitsProfile(
            household_size=3, current_monthly_income=500,
            enrolled_programs=["Medicaid"], state="TX",
        )
        assert calc_medicaid(0.0, profile) == 0.0
        assert calc_medicaid(20000.0, profile) == 0.0
        assert calc_medicaid(100000.0, profile) == 0.0


class TestCalcChip:
    """TX CHIP calculator edge cases."""

    def test_no_children_returns_zero(self):
        """No children means no CHIP benefit."""
        profile = BenefitsProfile(
            household_size=2, current_monthly_income=1000,
            dependents_under_6=0, dependents_6_to_17=0,
            enrolled_programs=["CHIP"], state="TX",
        )
        result = calc_chip(15000.0, profile)
        assert result == 0.0

    def test_with_children_low_income(self):
        """Children + low income should give CHIP benefit."""
        profile = BenefitsProfile(
            household_size=4, current_monthly_income=1000,
            dependents_under_6=1, dependents_6_to_17=1,
            enrolled_programs=["CHIP"], state="TX",
        )
        result = calc_chip(15000.0, profile)
        assert result > 0

    def test_with_children_over_fpl_limit(self):
        """Children but very high income should return zero."""
        profile = BenefitsProfile(
            household_size=4, current_monthly_income=10000,
            dependents_under_6=1, dependents_6_to_17=1,
            enrolled_programs=["CHIP"], state="TX",
        )
        result = calc_chip(200000.0, profile)
        assert result == 0.0


class TestCalcChildcare:
    """TX childcare subsidy edge cases."""

    def test_no_young_dependents_returns_zero(self):
        """No dependents_under_6 means no childcare subsidy."""
        profile = BenefitsProfile(
            household_size=3, current_monthly_income=1000,
            dependents_under_6=0, dependents_6_to_17=2,
            enrolled_programs=["Childcare_Subsidy"], state="TX",
        )
        result = calc_childcare(20000.0, profile)
        assert result == 0.0

    def test_above_smi_limit_returns_zero(self):
        """Income above 85% SMI should return zero."""
        profile = BenefitsProfile(
            household_size=3, current_monthly_income=8000,
            dependents_under_6=1,
            enrolled_programs=["Childcare_Subsidy"], state="TX",
        )
        result = calc_childcare(200000.0, profile)
        assert result == 0.0

    def test_low_income_with_dependents(self):
        """Low income + young children should give subsidy."""
        profile = BenefitsProfile(
            household_size=3, current_monthly_income=1000,
            dependents_under_6=2,
            enrolled_programs=["Childcare_Subsidy"], state="TX",
        )
        result = calc_childcare(15000.0, profile)
        assert result > 0


class TestCalcSection8:
    """TX Section 8 edge cases."""

    def test_above_ami_limit_returns_zero(self):
        """Income above 50% AMI should return zero."""
        profile = BenefitsProfile(
            household_size=4, current_monthly_income=8000,
            enrolled_programs=["Section_8"], state="TX",
        )
        result = calc_section_8(200000.0, profile)
        assert result == 0.0

    def test_low_income_gives_subsidy(self):
        """Low income should give a housing subsidy."""
        profile = BenefitsProfile(
            household_size=4, current_monthly_income=1000,
            enrolled_programs=["Section_8"], state="TX",
        )
        result = calc_section_8(12000.0, profile)
        assert result > 0


class TestCalcCeap:
    """TX CEAP (energy assistance) edge cases."""

    def test_above_fpl_limit_returns_zero(self):
        profile = BenefitsProfile(
            household_size=3, current_monthly_income=5000,
            enrolled_programs=["CEAP"], state="TX",
        )
        result = calc_ceap(100000.0, profile)
        assert result == 0.0

    def test_below_fpl_limit_returns_avg(self):
        profile = BenefitsProfile(
            household_size=3, current_monthly_income=500,
            enrolled_programs=["CEAP"], state="TX",
        )
        result = calc_ceap(6000.0, profile)
        assert result > 0


class TestSumProgramBenefits:
    """sum_program_benefits integration."""

    def test_sums_multiple_programs(self):
        profile = BenefitsProfile(
            household_size=3, current_monthly_income=1000,
            enrolled_programs=["SNAP", "CEAP"],
            state="TX",
        )
        total = sum_program_benefits(12000.0, profile)
        snap_alone = calc_snap(12000.0, profile)
        ceap_alone = calc_ceap(12000.0, profile)
        assert abs(total - (snap_alone + ceap_alone)) < 0.01

    def test_unknown_program_skipped(self):
        profile = BenefitsProfile(
            household_size=3, current_monthly_income=1000,
            enrolled_programs=["SNAP", "NONEXISTENT"],
            state="TX",
        )
        total = sum_program_benefits(12000.0, profile)
        snap_alone = calc_snap(12000.0, profile)
        assert abs(total - snap_alone) < 0.01

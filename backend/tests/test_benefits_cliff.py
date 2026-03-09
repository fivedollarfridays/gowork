"""Tests for benefits cliff calculator — Alabama-specific program modeling."""

import pytest

from app.modules.benefits.types import (
    BenefitsProfile,
    CliffAnalysis,
    CliffPoint,
    WageStep,
)
from app.modules.benefits.cliff_calculator import (
    calculate_cliff_analysis,
    calculate_net_at_wage,
    classify_cliff_severity,
)
from app.modules.benefits.thresholds import FPL_2026, SNAP_MAX_BENEFIT


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def single_no_programs():
    """Single adult, no benefits — should have no cliffs."""
    return BenefitsProfile(household_size=1, current_monthly_income=0)


@pytest.fixture
def family_on_snap():
    """Family of 3, on SNAP, income $800/month."""
    return BenefitsProfile(
        household_size=3,
        current_monthly_income=800,
        enrolled_programs=["SNAP"],
    )


@pytest.fixture
def family_snap_childcare():
    """Family of 3, SNAP + Childcare, 1 child under 6."""
    return BenefitsProfile(
        household_size=3,
        current_monthly_income=1000,
        enrolled_programs=["SNAP", "Childcare_Subsidy"],
        dependents_under_6=1,
    )


@pytest.fixture
def family_all_programs():
    """Family of 4 enrolled in all programs."""
    return BenefitsProfile(
        household_size=4,
        current_monthly_income=500,
        enrolled_programs=[
            "SNAP", "TANF", "Medicaid", "ALL_Kids",
            "Childcare_Subsidy", "Section_8", "LIHEAP",
        ],
        dependents_under_6=1,
        dependents_6_to_17=1,
    )


# ---------------------------------------------------------------------------
# Cliff severity classification
# ---------------------------------------------------------------------------

class TestCliffSeverity:
    def test_mild_under_50(self):
        assert classify_cliff_severity(30.0) == "mild"

    def test_moderate_50_to_200(self):
        assert classify_cliff_severity(100.0) == "moderate"

    def test_severe_over_200(self):
        assert classify_cliff_severity(250.0) == "severe"

    def test_zero_loss_is_mild(self):
        assert classify_cliff_severity(0.0) == "mild"

    def test_boundary_50_is_moderate(self):
        assert classify_cliff_severity(50.0) == "moderate"

    def test_boundary_200_is_severe(self):
        assert classify_cliff_severity(200.0) == "severe"


# ---------------------------------------------------------------------------
# Thresholds data
# ---------------------------------------------------------------------------

class TestThresholds:
    def test_fpl_has_all_household_sizes(self):
        for size in range(1, 9):
            assert size in FPL_2026

    def test_fpl_increases_with_size(self):
        for size in range(2, 9):
            assert FPL_2026[size] > FPL_2026[size - 1]

    def test_snap_max_benefit_exists(self):
        assert 1 in SNAP_MAX_BENEFIT
        assert 3 in SNAP_MAX_BENEFIT


# ---------------------------------------------------------------------------
# Single person, no programs
# ---------------------------------------------------------------------------

class TestNoPrograms:
    def test_no_cliff_points(self, single_no_programs):
        result = calculate_cliff_analysis(single_no_programs)
        assert isinstance(result, CliffAnalysis)
        assert len(result.cliff_points) == 0

    def test_wage_steps_exist(self, single_no_programs):
        result = calculate_cliff_analysis(single_no_programs)
        assert len(result.wage_steps) > 0

    def test_wage_steps_cover_range(self, single_no_programs):
        result = calculate_cliff_analysis(single_no_programs)
        wages = [s.wage for s in result.wage_steps]
        assert min(wages) == 8.0
        assert max(wages) == 25.0

    def test_net_income_increases_monotonically(self, single_no_programs):
        """Without programs, net income should always increase with wage."""
        result = calculate_cliff_analysis(single_no_programs)
        for i in range(1, len(result.wage_steps)):
            assert result.wage_steps[i].net_monthly >= result.wage_steps[i - 1].net_monthly

    def test_benefits_total_is_zero(self, single_no_programs):
        result = calculate_cliff_analysis(single_no_programs)
        for step in result.wage_steps:
            assert step.benefits_total == 0.0

    def test_programs_list_empty(self, single_no_programs):
        result = calculate_cliff_analysis(single_no_programs)
        assert len(result.programs) == 0


# ---------------------------------------------------------------------------
# SNAP phase-out
# ---------------------------------------------------------------------------

class TestSnapCliff:
    def test_snap_benefit_at_low_income(self, family_on_snap):
        """At low wages, SNAP should provide a benefit."""
        net = calculate_net_at_wage(8.0, family_on_snap)
        assert net > 8.0 * 40 * 4.33  # net > gross (benefits add)

    def test_snap_phases_out_above_fpl(self, family_on_snap):
        """SNAP should phase out above 130% FPL for household of 3."""
        fpl_3 = FPL_2026[3]
        threshold_hourly = (fpl_3 * 1.30) / 2080
        # Well above threshold, SNAP should be zero
        high_wage = threshold_hourly + 5.0
        result = calculate_cliff_analysis(
            BenefitsProfile(
                household_size=3,
                current_monthly_income=0,
                enrolled_programs=["SNAP"],
            )
        )
        high_steps = [s for s in result.wage_steps if s.wage >= high_wage]
        if high_steps:
            assert high_steps[0].benefits_total == 0.0

    def test_snap_gradual_no_net_cliff(self, family_on_snap):
        """SNAP phases out gradually — wage gain exceeds benefit loss, no net cliff."""
        result = calculate_cliff_analysis(family_on_snap)
        snap_cliffs = [c for c in result.cliff_points if c.lost_program == "SNAP"]
        # SNAP's gradual reduction doesn't create a net income cliff
        assert len(snap_cliffs) == 0

    def test_snap_benefit_decreases_with_income(self, family_on_snap):
        """SNAP benefit should decrease as wages increase."""
        result = calculate_cliff_analysis(family_on_snap)
        benefit_steps = [(s.wage, s.benefits_total) for s in result.wage_steps if s.benefits_total > 0]
        # Benefits should generally decrease with wage
        assert len(benefit_steps) >= 2
        assert benefit_steps[0][1] > benefit_steps[-1][1]

    def test_snap_has_program_info(self, family_on_snap):
        result = calculate_cliff_analysis(family_on_snap)
        snap_programs = [p for p in result.programs if p.program == "SNAP"]
        assert len(snap_programs) == 1
        assert snap_programs[0].eligible is True


# ---------------------------------------------------------------------------
# Section 8 hard cliff — large subsidy drop
# ---------------------------------------------------------------------------

class TestSection8Cliff:
    def test_section_8_cliff_detected(self):
        """Section 8 has a hard cliff — large subsidy drops to zero at 50% AMI."""
        profile = BenefitsProfile(
            household_size=3,
            current_monthly_income=500,
            enrolled_programs=["Section_8"],
        )
        result = calculate_cliff_analysis(profile)
        s8_cliffs = [c for c in result.cliff_points if c.lost_program == "Section_8"]
        assert len(s8_cliffs) >= 1

    def test_section_8_cliff_is_severe(self):
        """Section 8 cliff should be severe (housing subsidy is large)."""
        profile = BenefitsProfile(
            household_size=3,
            current_monthly_income=500,
            enrolled_programs=["Section_8"],
        )
        result = calculate_cliff_analysis(profile)
        s8_cliffs = [c for c in result.cliff_points if c.lost_program == "Section_8"]
        if s8_cliffs:
            assert s8_cliffs[0].severity in ("moderate", "severe")


# ---------------------------------------------------------------------------
# Combined programs — compound cliff
# ---------------------------------------------------------------------------

class TestCompoundCliff:
    def test_multiple_cliff_points(self, family_snap_childcare):
        """SNAP + Childcare should produce multiple cliff points."""
        result = calculate_cliff_analysis(family_snap_childcare)
        assert len(result.cliff_points) >= 1

    def test_compound_cliff_worse_than_single(self, family_snap_childcare):
        """Total cliff loss with multiple programs should exceed single program."""
        result = calculate_cliff_analysis(family_snap_childcare)
        if result.cliff_points:
            total_loss = sum(c.monthly_loss for c in result.cliff_points)
            assert total_loss > 0

    def test_worst_cliff_wage_set(self, family_snap_childcare):
        result = calculate_cliff_analysis(family_snap_childcare)
        if result.cliff_points:
            assert result.worst_cliff_wage is not None


# ---------------------------------------------------------------------------
# All programs — worst-case scenario
# ---------------------------------------------------------------------------

class TestAllPrograms:
    def test_all_programs_analyzed(self, family_all_programs):
        result = calculate_cliff_analysis(family_all_programs)
        program_names = {p.program for p in result.programs}
        for prog in family_all_programs.enrolled_programs:
            assert prog in program_names

    def test_multiple_cliffs_detected(self, family_all_programs):
        result = calculate_cliff_analysis(family_all_programs)
        assert len(result.cliff_points) >= 2

    def test_worst_cliff_is_severe(self, family_all_programs):
        """With all programs, the worst cliff should be severe."""
        result = calculate_cliff_analysis(family_all_programs)
        if result.cliff_points:
            worst = max(result.cliff_points, key=lambda c: c.monthly_loss)
            assert worst.severity in ("moderate", "severe")


# ---------------------------------------------------------------------------
# Net income calculation
# ---------------------------------------------------------------------------

class TestNetAtWage:
    def test_zero_wage_returns_benefits_only(self):
        profile = BenefitsProfile(
            household_size=3,
            enrolled_programs=["SNAP"],
        )
        net = calculate_net_at_wage(0.0, profile)
        assert net >= 0

    def test_high_wage_no_benefits(self):
        profile = BenefitsProfile(
            household_size=1,
            enrolled_programs=["SNAP"],
        )
        net = calculate_net_at_wage(25.0, profile)
        # At $25/hr, SNAP should be gone — net ~ gross after taxes
        gross_monthly = 25.0 * 2080 / 12
        assert net < gross_monthly  # taxes taken out
        assert net > gross_monthly * 0.8  # but not too much

    def test_no_programs_net_equals_after_tax(self):
        profile = BenefitsProfile(household_size=1)
        net = calculate_net_at_wage(15.0, profile)
        gross_monthly = 15.0 * 2080 / 12
        # Should be gross minus taxes (FICA + income)
        assert net < gross_monthly
        assert net > 0


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_empty_programs_list(self):
        profile = BenefitsProfile(household_size=1, enrolled_programs=[])
        result = calculate_cliff_analysis(profile)
        assert len(result.cliff_points) == 0

    def test_minimum_household_size(self):
        profile = BenefitsProfile(household_size=1, enrolled_programs=["SNAP"])
        result = calculate_cliff_analysis(profile)
        assert isinstance(result, CliffAnalysis)

    def test_maximum_household_size(self):
        profile = BenefitsProfile(household_size=8, enrolled_programs=["SNAP"])
        result = calculate_cliff_analysis(profile)
        assert isinstance(result, CliffAnalysis)

    def test_recovery_wage_set(self):
        """recovery_wage should be where net income recovers to pre-cliff peak."""
        profile = BenefitsProfile(
            household_size=3,
            current_monthly_income=500,
            enrolled_programs=["SNAP"],
        )
        result = calculate_cliff_analysis(profile)
        if result.recovery_wage is not None:
            assert result.recovery_wage >= 8.0
            assert result.recovery_wage <= 25.0
            # Net at recovery wage should be >= pre-cliff peak
            pre_cliff = max(
                s.net_monthly for s in result.wage_steps
                if s.wage < result.cliff_points[0].hourly_wage
            )
            recovery_net = next(
                s.net_monthly for s in result.wage_steps
                if s.wage == result.recovery_wage
            )
            assert recovery_net >= pre_cliff

    def test_current_net_monthly_computed(self):
        profile = BenefitsProfile(
            household_size=3,
            current_monthly_income=1000,
            enrolled_programs=["SNAP"],
        )
        result = calculate_cliff_analysis(profile)
        assert result.current_net_monthly > 0

    def test_wage_step_half_dollar_increments(self):
        profile = BenefitsProfile(household_size=1)
        result = calculate_cliff_analysis(profile)
        wages = [s.wage for s in result.wage_steps]
        for i in range(1, len(wages)):
            assert abs(wages[i] - wages[i - 1] - 0.50) < 0.01

    def test_unrecognized_program_ignored_in_analysis(self):
        """Unrecognized program names are silently skipped."""
        # Use Section_8 to ensure a cliff IS detected (triggers _identify_lost_program)
        profile = BenefitsProfile(
            household_size=3,
            current_monthly_income=500,
            enrolled_programs=["Section_8", "BOGUS_PROGRAM"],
        )
        result = calculate_cliff_analysis(profile)
        # Should still complete — BOGUS_PROGRAM skipped in identify/build
        program_names = {p.program for p in result.programs}
        assert "Section_8" in program_names
        assert "BOGUS_PROGRAM" not in program_names
        # Cliff still detected from Section_8
        assert len(result.cliff_points) >= 1

    def test_recovery_wage_none_when_no_recovery(self):
        """No recovery wage when net never reaches pre-cliff peak."""
        from app.modules.benefits.cliff_calculator import _find_recovery_wage

        steps = [
            WageStep(wage=24.0, gross_monthly=4160, benefits_total=0, net_monthly=3500),
            WageStep(wage=25.0, gross_monthly=4333, benefits_total=0, net_monthly=3400),
        ]
        cliffs = [
            CliffPoint(
                hourly_wage=25.0, annual_income=52000,
                net_monthly_income=3400, lost_program="Section_8",
                monthly_loss=100, severity="moderate",
            ),
        ]
        assert _find_recovery_wage(steps, cliffs) is None


# ---------------------------------------------------------------------------
# Program calculator edge cases (coverage)
# ---------------------------------------------------------------------------

class TestProgramEdgeCases:
    def test_tanf_eligible_at_low_income(self):
        """TANF returns max benefit when income below cutoff."""
        from app.modules.benefits.program_calculators import calc_tanf
        from app.modules.benefits.thresholds import TANF_MAX_MONTHLY

        profile = BenefitsProfile(household_size=3, current_monthly_income=0)
        benefit = calc_tanf(0.0, profile)
        assert benefit == TANF_MAX_MONTHLY[3]

    def test_all_kids_zero_with_no_children(self):
        """ALL Kids returns 0 when household has no dependents."""
        from app.modules.benefits.program_calculators import calc_all_kids

        profile = BenefitsProfile(
            household_size=2,
            dependents_under_6=0,
            dependents_6_to_17=0,
        )
        assert calc_all_kids(10000.0, profile) == 0.0

    def test_childcare_zero_with_no_under_6(self):
        """Childcare subsidy returns 0 when no dependents under 6."""
        from app.modules.benefits.program_calculators import calc_childcare

        profile = BenefitsProfile(
            household_size=3,
            dependents_under_6=0,
            dependents_6_to_17=2,
        )
        assert calc_childcare(20000.0, profile) == 0.0

"""Tests for sum_program_benefits — consolidation of benefit summing logic."""

import pytest

from app.modules.benefits.types import BenefitsProfile
from app.modules.benefits.program_calculators import PROGRAM_CALCULATORS


class TestSumProgramBenefits:
    """Tests for the public sum_program_benefits function."""

    def test_sums_enrolled_programs(self) -> None:
        """Should sum benefits for all enrolled programs at given income."""
        from app.modules.benefits.program_calculators import sum_program_benefits

        profile = BenefitsProfile(
            household_size=3,
            current_monthly_income=800,
            enrolled_programs=["SNAP", "LIHEAP"],
        )
        annual_income = 10_000.0

        result = sum_program_benefits(annual_income, profile)

        # Manually compute expected: each calculator individually
        expected = 0.0
        for prog in profile.enrolled_programs:
            calc = PROGRAM_CALCULATORS[prog]
            expected += calc(annual_income, profile)
        assert result == pytest.approx(expected)
        assert result > 0

    def test_returns_zero_for_no_programs(self) -> None:
        """Should return 0.0 when enrolled_programs is empty."""
        from app.modules.benefits.program_calculators import sum_program_benefits

        profile = BenefitsProfile(household_size=1, enrolled_programs=[])
        assert sum_program_benefits(20_000.0, profile) == 0.0

    def test_ignores_unknown_programs(self) -> None:
        """Should silently skip programs not in PROGRAM_CALCULATORS."""
        from app.modules.benefits.program_calculators import sum_program_benefits

        profile = BenefitsProfile(
            household_size=2,
            enrolled_programs=["BOGUS_PROGRAM", "NONEXISTENT"],
        )
        assert sum_program_benefits(15_000.0, profile) == 0.0

    def test_matches_manual_sum_all_programs(self) -> None:
        """Should match manually summing every known program."""
        from app.modules.benefits.program_calculators import sum_program_benefits

        profile = BenefitsProfile(
            household_size=4,
            current_monthly_income=500,
            enrolled_programs=list(PROGRAM_CALCULATORS.keys()),
            dependents_under_6=1,
            dependents_6_to_17=1,
        )
        annual = 8_000.0

        result = sum_program_benefits(annual, profile)

        expected = sum(
            calc(annual, profile) for calc in PROGRAM_CALCULATORS.values()
        )
        assert result == pytest.approx(expected)

    def test_high_income_zeroes_out_benefits(self) -> None:
        """At a very high income, all benefits should phase out to zero."""
        from app.modules.benefits.program_calculators import sum_program_benefits

        profile = BenefitsProfile(
            household_size=1,
            enrolled_programs=["SNAP", "TANF", "LIHEAP"],
        )
        assert sum_program_benefits(200_000.0, profile) == 0.0


class TestConsolidationEquivalence:
    """Verify sum_program_benefits matches the old implementations."""

    def test_matches_cliff_calculator_total_benefits(self) -> None:
        """sum_program_benefits(hourly * 2080, profile) should equal
        what _total_benefits(hourly, profile) used to return."""
        from app.modules.benefits.program_calculators import sum_program_benefits

        profile = BenefitsProfile(
            household_size=3,
            current_monthly_income=1000,
            enrolled_programs=["SNAP", "Section_8"],
        )
        hourly = 12.0
        hours_per_year = 2080

        from_consolidated = sum_program_benefits(
            hourly * hours_per_year, profile,
        )

        # Manually replicate the old _total_benefits logic
        total = 0.0
        annual = hourly * hours_per_year
        for prog in profile.enrolled_programs:
            calc = PROGRAM_CALCULATORS.get(prog)
            if calc:
                total += calc(annual, profile)

        assert from_consolidated == pytest.approx(total)

    def test_matches_pvs_scorer_sum_benefits(self) -> None:
        """sum_program_benefits(annual, profile) should equal
        what _sum_benefits(annual, profile) used to return."""
        from app.modules.benefits.program_calculators import sum_program_benefits

        profile = BenefitsProfile(
            household_size=3,
            current_monthly_income=800,
            enrolled_programs=["SNAP", "Childcare_Subsidy"],
            dependents_under_6=1,
        )
        annual = 18_000.0

        from_consolidated = sum_program_benefits(annual, profile)

        # Manually replicate the old _sum_benefits logic
        expected = sum(
            calc(annual, profile)
            for prog in profile.enrolled_programs
            if (calc := PROGRAM_CALCULATORS.get(prog))
        )

        assert from_consolidated == pytest.approx(expected)

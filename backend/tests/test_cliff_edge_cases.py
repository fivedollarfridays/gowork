"""Edge-case tests for benefits cliff calculator.

Targets:
- Wage at exact boundary ($8.00 min, $25.00 max)
- Profile with zero enrolled programs
- Profile with all 7 TX programs (CHIP/CEAP)
- Profile with all 7 AL programs (ALL_Kids/LIHEAP)
- Household size 1 vs 8
- Unknown program in enrolled list (covers lines 143, 160)
- Zero income profile
- Recovery wage detection
"""

import pytest
from unittest.mock import patch

from app.cities.config import CityConfig
from app.modules.benefits.types import BenefitsProfile, CliffAnalysis


def _mock_tx():
    return CityConfig(
        name="Fort Worth", state="TX", location="Fort Worth, TX",
        zip_ranges=["76101-76199"], job_adapters=["twc"],
        data_dir="data/cities/fort-worth",
    )


def _mock_al():
    return CityConfig(
        name="Montgomery", state="AL", location="Montgomery, AL",
        zip_ranges=["36101-36120"], job_adapters=["brightdata"],
        data_dir="data/cities/montgomery",
    )


@pytest.fixture
def _fort_worth(monkeypatch):
    monkeypatch.setenv("CITY", "fort-worth")
    from app.cities.config import load_city_config
    load_city_config.cache_clear()
    from app.core.config import get_settings
    get_settings.cache_clear()
    yield
    load_city_config.cache_clear()
    get_settings.cache_clear()


@pytest.fixture
def _montgomery(monkeypatch):
    monkeypatch.setenv("CITY", "montgomery")
    from app.cities.config import load_city_config
    load_city_config.cache_clear()
    from app.core.config import get_settings
    get_settings.cache_clear()
    yield
    load_city_config.cache_clear()
    get_settings.cache_clear()


class TestCliffBoundaryWages:
    """Wages at exact min/max boundaries."""

    @pytest.mark.usefixtures("_fort_worth")
    def test_wage_min_8_dollars(self):
        """$8.00/hr should be the first wage step."""
        from app.modules.benefits.cliff_calculator import calculate_cliff_analysis

        profile = BenefitsProfile(
            household_size=3, current_monthly_income=1200,
            enrolled_programs=["SNAP"], state="TX",
        )
        result = calculate_cliff_analysis(profile)
        assert result.wage_steps[0].wage == 8.0

    @pytest.mark.usefixtures("_fort_worth")
    def test_wage_max_25_dollars(self):
        """$25.00/hr should be the last wage step."""
        from app.modules.benefits.cliff_calculator import calculate_cliff_analysis

        profile = BenefitsProfile(
            household_size=3, current_monthly_income=1200,
            enrolled_programs=["SNAP"], state="TX",
        )
        result = calculate_cliff_analysis(profile)
        assert result.wage_steps[-1].wage == 25.0

    @pytest.mark.usefixtures("_fort_worth")
    def test_all_wage_steps_have_positive_gross(self):
        """Every wage step should have positive gross monthly income."""
        from app.modules.benefits.cliff_calculator import calculate_cliff_analysis

        profile = BenefitsProfile(
            household_size=2, current_monthly_income=1500,
            enrolled_programs=["SNAP"], state="TX",
        )
        result = calculate_cliff_analysis(profile)
        for step in result.wage_steps:
            assert step.gross_monthly > 0


class TestCliffZeroPrograms:
    """Profile with zero enrolled programs."""

    @pytest.mark.usefixtures("_fort_worth")
    def test_no_programs_produces_no_cliffs(self):
        """Zero programs means no benefit loss, so zero cliff points."""
        from app.modules.benefits.cliff_calculator import calculate_cliff_analysis

        profile = BenefitsProfile(
            household_size=3, current_monthly_income=1500,
            enrolled_programs=[], state="TX",
        )
        result = calculate_cliff_analysis(profile)
        assert result.cliff_points == []
        assert result.programs == []
        assert result.worst_cliff_wage is None
        assert result.recovery_wage is None

    @pytest.mark.usefixtures("_fort_worth")
    def test_no_programs_still_has_wage_steps(self):
        """Even with no programs, wage steps should be generated."""
        from app.modules.benefits.cliff_calculator import calculate_cliff_analysis

        profile = BenefitsProfile(
            household_size=1, current_monthly_income=1000,
            enrolled_programs=[], state="TX",
        )
        result = calculate_cliff_analysis(profile)
        assert len(result.wage_steps) > 0


class TestCliffAllPrograms:
    """Profile with all 7 programs enrolled."""

    @pytest.mark.usefixtures("_fort_worth")
    def test_all_tx_programs(self):
        """All 7 TX programs should produce a valid analysis."""
        from app.modules.benefits.cliff_calculator import calculate_cliff_analysis

        profile = BenefitsProfile(
            household_size=4, current_monthly_income=800,
            enrolled_programs=[
                "SNAP", "TANF", "Medicaid", "CHIP",
                "Childcare_Subsidy", "Section_8", "CEAP",
            ],
            dependents_under_6=1, dependents_6_to_17=1,
            state="TX",
        )
        result = calculate_cliff_analysis(profile)
        assert isinstance(result, CliffAnalysis)
        # Should have programs in the list (though some may show $0 value)
        assert len(result.programs) >= 5

    @pytest.mark.usefixtures("_montgomery")
    def test_all_al_programs(self):
        """All 7 AL programs should produce a valid analysis."""
        from app.modules.benefits.cliff_calculator import calculate_cliff_analysis

        profile = BenefitsProfile(
            household_size=4, current_monthly_income=800,
            enrolled_programs=[
                "SNAP", "TANF", "Medicaid", "ALL_Kids",
                "Childcare_Subsidy", "Section_8", "LIHEAP",
            ],
            dependents_under_6=1, dependents_6_to_17=1,
            state="AL",
        )
        result = calculate_cliff_analysis(profile)
        assert isinstance(result, CliffAnalysis)
        assert len(result.programs) >= 5


class TestCliffUnknownProgram:
    """Unknown program in enrolled list -- covers lines 143, 160."""

    @pytest.mark.usefixtures("_fort_worth")
    def test_unknown_program_skipped_in_programs(self):
        """Unknown program should be silently skipped in program list."""
        from app.modules.benefits.cliff_calculator import calculate_cliff_analysis

        profile = BenefitsProfile(
            household_size=3, current_monthly_income=1500,
            enrolled_programs=["SNAP", "FAKE_PROGRAM"],
            state="TX",
        )
        result = calculate_cliff_analysis(profile)
        prog_names = {p.program for p in result.programs}
        assert "SNAP" in prog_names
        assert "FAKE_PROGRAM" not in prog_names

    @pytest.mark.usefixtures("_fort_worth")
    def test_unknown_program_skipped_in_cliff_detection(self):
        """Unknown program should not crash cliff detection."""
        from app.modules.benefits.cliff_calculator import calculate_cliff_analysis

        profile = BenefitsProfile(
            household_size=3, current_monthly_income=1200,
            enrolled_programs=["SNAP", "NONEXISTENT"],
            state="TX",
        )
        result = calculate_cliff_analysis(profile)
        # Should not crash and should still have valid steps
        assert len(result.wage_steps) > 0


class TestCliffHouseholdSizes:
    """Household size 1 (min) and 8 (max)."""

    @pytest.mark.usefixtures("_fort_worth")
    def test_household_size_1(self):
        """Single-person household cliff analysis."""
        from app.modules.benefits.cliff_calculator import calculate_cliff_analysis

        profile = BenefitsProfile(
            household_size=1, current_monthly_income=800,
            enrolled_programs=["SNAP", "CEAP"], state="TX",
        )
        result = calculate_cliff_analysis(profile)
        assert isinstance(result, CliffAnalysis)
        assert len(result.wage_steps) > 0

    @pytest.mark.usefixtures("_fort_worth")
    def test_household_size_8(self):
        """Maximum household size cliff analysis."""
        from app.modules.benefits.cliff_calculator import calculate_cliff_analysis

        profile = BenefitsProfile(
            household_size=8, current_monthly_income=2000,
            enrolled_programs=["SNAP", "Section_8"], state="TX",
        )
        result = calculate_cliff_analysis(profile)
        assert isinstance(result, CliffAnalysis)
        assert len(result.wage_steps) > 0


class TestCliffZeroIncome:
    """Profile with zero current income."""

    @pytest.mark.usefixtures("_fort_worth")
    def test_zero_income(self):
        """Zero income should produce $0 current net."""
        from app.modules.benefits.cliff_calculator import calculate_cliff_analysis

        profile = BenefitsProfile(
            household_size=3, current_monthly_income=0,
            enrolled_programs=["SNAP"], state="TX",
        )
        result = calculate_cliff_analysis(profile)
        assert result.current_net_monthly == 0.0


class TestCliffSeverityClassification:
    """Cliff severity classification edge cases."""

    def test_severe_threshold(self):
        from app.modules.benefits.cliff_calculator import classify_cliff_severity
        from app.modules.benefits.types import CliffSeverity

        assert classify_cliff_severity(200.0) == CliffSeverity.SEVERE
        assert classify_cliff_severity(500.0) == CliffSeverity.SEVERE

    def test_moderate_threshold(self):
        from app.modules.benefits.cliff_calculator import classify_cliff_severity
        from app.modules.benefits.types import CliffSeverity

        assert classify_cliff_severity(50.0) == CliffSeverity.MODERATE
        assert classify_cliff_severity(199.99) == CliffSeverity.MODERATE

    def test_mild_threshold(self):
        from app.modules.benefits.cliff_calculator import classify_cliff_severity
        from app.modules.benefits.types import CliffSeverity

        assert classify_cliff_severity(10.0) == CliffSeverity.MILD
        assert classify_cliff_severity(49.99) == CliffSeverity.MILD
        assert classify_cliff_severity(0.0) == CliffSeverity.MILD


class TestCliffRecoveryWage:
    """Recovery wage detection."""

    @pytest.mark.usefixtures("_fort_worth")
    def test_no_cliffs_means_no_recovery(self):
        """No cliffs means recovery_wage is None."""
        from app.modules.benefits.cliff_calculator import calculate_cliff_analysis

        profile = BenefitsProfile(
            household_size=3, current_monthly_income=1500,
            enrolled_programs=[], state="TX",
        )
        result = calculate_cliff_analysis(profile)
        assert result.recovery_wage is None

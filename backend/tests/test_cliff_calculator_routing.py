"""Tests for cliff calculator city-aware routing.

Verifies that cliff_calculator uses the benefits router to get thresholds
and calculators based on the active city, not direct Alabama imports.
"""

import pytest
from unittest.mock import patch

from app.modules.benefits.types import BenefitsProfile, CliffAnalysis


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tx_profile():
    """Fort Worth family profile using TX program names."""
    return BenefitsProfile(
        household_size=4,
        current_monthly_income=2000,
        enrolled_programs=["SNAP", "Section_8"],
        state="TX",
    )


@pytest.fixture
def tx_profile_chip():
    """Fort Worth profile with CHIP (TX equivalent of ALL_Kids)."""
    return BenefitsProfile(
        household_size=4,
        current_monthly_income=1500,
        enrolled_programs=["SNAP", "CHIP"],
        dependents_under_6=1,
        dependents_6_to_17=1,
        state="TX",
    )


@pytest.fixture
def tx_profile_ceap():
    """Fort Worth profile with CEAP (TX equivalent of LIHEAP)."""
    return BenefitsProfile(
        household_size=3,
        current_monthly_income=800,
        enrolled_programs=["SNAP", "CEAP"],
        state="TX",
    )


@pytest.fixture
def al_profile():
    """Montgomery family profile using AL program names."""
    return BenefitsProfile(
        household_size=4,
        current_monthly_income=2000,
        enrolled_programs=["SNAP", "Section_8"],
        state="AL",
    )


@pytest.fixture
def _fort_worth_city(monkeypatch):
    """Set CITY=fort-worth for the test."""
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
    """Set CITY=montgomery for the test."""
    monkeypatch.setenv("CITY", "montgomery")
    from app.cities.config import load_city_config
    load_city_config.cache_clear()
    from app.core.config import get_settings
    get_settings.cache_clear()
    yield
    load_city_config.cache_clear()
    get_settings.cache_clear()


# ---------------------------------------------------------------------------
# TX vs AL Section 8 AMI difference
# ---------------------------------------------------------------------------

class TestCliffCalculatorRouting:
    """Verify cliff calculator uses routed thresholds based on city."""

    @pytest.mark.usefixtures("_fort_worth_city")
    def test_fort_worth_section8_uses_tx_ami(self, tx_profile):
        """CITY=fort-worth Section 8 cliff should use TX AMI (~$78K for hs=4)."""
        from app.modules.benefits.cliff_calculator import calculate_cliff_analysis

        result = calculate_cliff_analysis(tx_profile)
        assert isinstance(result, CliffAnalysis)
        # TX AMI for hs=4 is $78K, so 50% = $39K => ~$18.75/hr
        # AL AMI for hs=4 is $60K, so 50% = $30K => ~$14.42/hr
        # Section 8 cliff should occur at a HIGHER wage for TX
        s8_cliffs = [c for c in result.cliff_points if c.lost_program == "Section_8"]
        if s8_cliffs:
            # TX cliff wage should be above $17/hr (reflecting higher AMI)
            assert s8_cliffs[0].hourly_wage > 17.0

    @pytest.mark.usefixtures("_montgomery_city")
    def test_montgomery_section8_uses_al_ami(self, al_profile):
        """CITY=montgomery Section 8 cliff should use AL AMI (~$60K for hs=4)."""
        from app.modules.benefits.cliff_calculator import calculate_cliff_analysis

        result = calculate_cliff_analysis(al_profile)
        assert isinstance(result, CliffAnalysis)
        s8_cliffs = [c for c in result.cliff_points if c.lost_program == "Section_8"]
        if s8_cliffs:
            # AL cliff wage should be below $16/hr (reflecting lower AMI)
            assert s8_cliffs[0].hourly_wage < 16.0

    @pytest.mark.usefixtures("_fort_worth_city")
    def test_fort_worth_chip_recognized(self, tx_profile_chip):
        """CITY=fort-worth should handle CHIP program (TX equiv of ALL_Kids)."""
        from app.modules.benefits.cliff_calculator import calculate_cliff_analysis

        result = calculate_cliff_analysis(tx_profile_chip)
        assert isinstance(result, CliffAnalysis)
        # CHIP should appear in programs list
        program_names = {p.program for p in result.programs}
        assert "CHIP" in program_names

    @pytest.mark.usefixtures("_fort_worth_city")
    def test_fort_worth_ceap_recognized(self, tx_profile_ceap):
        """CITY=fort-worth should handle CEAP program (TX equiv of LIHEAP)."""
        from app.modules.benefits.cliff_calculator import calculate_cliff_analysis

        result = calculate_cliff_analysis(tx_profile_ceap)
        assert isinstance(result, CliffAnalysis)
        program_names = {p.program for p in result.programs}
        assert "CEAP" in program_names

    @pytest.mark.usefixtures("_fort_worth_city")
    def test_fort_worth_phase_out_handles_chip(self, tx_profile_chip):
        """_get_phase_out should return valid data for CHIP (not just ALL_Kids)."""
        from app.modules.benefits.cliff_calculator import calculate_cliff_analysis

        result = calculate_cliff_analysis(tx_profile_chip)
        chip_programs = [p for p in result.programs if p.program == "CHIP"]
        assert len(chip_programs) == 1
        assert chip_programs[0].phase_out_start > 0
        assert chip_programs[0].phase_out_end >= chip_programs[0].phase_out_start

    @pytest.mark.usefixtures("_fort_worth_city")
    def test_fort_worth_phase_out_handles_ceap(self, tx_profile_ceap):
        """_get_phase_out should return valid data for CEAP (not just LIHEAP)."""
        from app.modules.benefits.cliff_calculator import calculate_cliff_analysis

        result = calculate_cliff_analysis(tx_profile_ceap)
        ceap_programs = [p for p in result.programs if p.program == "CEAP"]
        assert len(ceap_programs) == 1
        assert ceap_programs[0].phase_out_start > 0

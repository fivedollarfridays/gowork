"""Tests for cliff calculator handling of unknown programs.

Bypasses BenefitsProfile validation to reach the defensive guards
at cliff_calculator.py lines 143 and 160 where calc is None.
"""

import pytest

from app.modules.benefits.types import BenefitsProfile


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


class TestCliffUnknownProgramDefense:
    """Bypass validation to test defensive guards for unknown programs."""

    @pytest.mark.usefixtures("_fort_worth")
    def test_unknown_program_skipped_in_build_program_list(self):
        """Line 160: unknown program calc is None -> skip in _build_program_list."""
        from app.modules.benefits.cliff_calculator import calculate_cliff_analysis

        # Bypass Pydantic validation to inject unknown program
        profile = BenefitsProfile.model_construct(
            household_size=3,
            current_monthly_income=1500,
            enrolled_programs=["SNAP", "UNKNOWN_PROGRAM"],
            dependents_under_6=0,
            dependents_6_to_17=0,
            state="TX",
        )
        result = calculate_cliff_analysis(profile)
        # UNKNOWN_PROGRAM should be skipped, only SNAP appears
        prog_names = {p.program for p in result.programs}
        assert "SNAP" in prog_names
        assert "UNKNOWN_PROGRAM" not in prog_names

    @pytest.mark.usefixtures("_fort_worth")
    def test_unknown_program_skipped_in_identify_lost(self):
        """Line 143: unknown program calc is None -> skip in _identify_lost_program.

        Uses CEAP (hard cliff at 150% FPL) plus an unknown program.
        When the cliff fires, _identify_lost_program iterates all
        enrolled programs including the unknown one, hitting the None guard.
        """
        from app.modules.benefits.cliff_calculator import calculate_cliff_analysis

        # CEAP has a hard cliff: hs=1 at 150% FPL
        profile = BenefitsProfile.model_construct(
            household_size=1,
            current_monthly_income=600,
            enrolled_programs=["CEAP", "BOGUS_PROGRAM"],
            dependents_under_6=0,
            dependents_6_to_17=0,
            state="TX",
        )
        result = calculate_cliff_analysis(profile)
        # CEAP cliff should fire; BOGUS_PROGRAM should be skipped
        assert len(result.cliff_points) >= 1
        for cliff in result.cliff_points:
            assert cliff.lost_program != "BOGUS_PROGRAM"

    @pytest.mark.usefixtures("_fort_worth")
    def test_unknown_only_programs(self):
        """All enrolled programs are unknown -> empty programs list, no cliffs."""
        from app.modules.benefits.cliff_calculator import calculate_cliff_analysis

        profile = BenefitsProfile.model_construct(
            household_size=2,
            current_monthly_income=1000,
            enrolled_programs=["FAKE_A", "FAKE_B"],
            dependents_under_6=0,
            dependents_6_to_17=0,
            state="TX",
        )
        result = calculate_cliff_analysis(profile)
        assert result.programs == []
        assert result.cliff_points == []

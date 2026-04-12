"""Integration test -- full Fort Worth pipeline verification.

Sets CITY=fort-worth and verifies all Texas-specific content flows correctly
through the entire system.
"""

import pytest
from unittest.mock import patch
from app.cities.config import CityConfig


def _fw_config():
    return CityConfig(
        name="Fort Worth", state="TX", location="Fort Worth, TX",
        zip_ranges=["76101-76199"], job_adapters=["twc", "usajobs"],
        data_dir="data/cities/fort-worth",
    )


def _al_config():
    return CityConfig(
        name="Montgomery", state="AL", location="Montgomery, AL",
        zip_ranges=["36101-36120", "36130", "36140-36142"],
        job_adapters=["brightdata", "honestjobs"],
        data_dir="data/cities/montgomery",
    )


class TestFortWorthBenefitsIntegration:
    def test_tx_benefits_screener_returns_chip(self):
        """CITY=fort-worth should yield CHIP, not ALL_Kids."""
        from app.modules.benefits.router import get_program_checks

        with patch("app.modules.benefits.router.get_city_config", return_value=_fw_config()):
            checks = get_program_checks()
            assert "CHIP" in checks
            assert "ALL_Kids" not in checks
            assert "CEAP" in checks
            assert "LIHEAP" not in checks

    def test_tx_application_data_has_hhsc(self):
        from app.modules.benefits.router import get_application_data

        with patch("app.modules.benefits.router.get_city_config", return_value=_fw_config()):
            data = get_application_data()
            snap = data["SNAP"]
            assert "yourtexasbenefits" in snap.application_url
            assert "Fort Worth" in snap.office_address or "TX" in snap.office_address

    def test_tx_disclaimer_mentions_hhsc(self):
        from app.modules.benefits.router import get_screener_disclaimer

        with patch("app.modules.benefits.router.get_city_config", return_value=_fw_config()):
            disclaimer = get_screener_disclaimer()
            assert "HHSC" in disclaimer or "Texas" in disclaimer


class TestFortWorthCriminalIntegration:
    def test_tx_record_clearing_returns_dual_result(self):
        from app.modules.criminal.router import check_record_clearing
        from app.modules.criminal.record_profile import RecordProfile, RecordType, ChargeCategory
        from app.modules.criminal.texas_expunction import TexasRecordClearingResult

        profile = RecordProfile(
            record_types=[RecordType.ARREST_ONLY],
            charge_categories=[ChargeCategory.OTHER],
        )
        with patch("app.modules.criminal.router.get_city_config", return_value=_fw_config()):
            result = check_record_clearing(profile)
            assert isinstance(result, TexasRecordClearingResult)
            assert result.expunction_eligible  # arrest-only = eligible


class TestFortWorthGeoIntegration:
    def test_fw_zip_validation_accepts_761xx(self):
        from app.modules.matching.zip_validation import is_valid_zip_for_city

        assert is_valid_zip_for_city("76102", _fw_config())
        assert not is_valid_zip_for_city("36104", _fw_config())

    def test_fw_downtown_coords_in_fort_worth(self):
        from app.modules.matching.geo_router import get_downtown_coords

        with patch("app.modules.matching.geo_router.get_city_config", return_value=_fw_config()):
            lat, lng = get_downtown_coords()
            assert 32.7 < lat < 32.8  # Fort Worth latitude
            assert -97.4 < lng < -97.3  # Fort Worth longitude


class TestFortWorthResourceIntegration:
    def test_fw_career_center_is_workforce_solutions(self):
        from app.modules.matching.resource_router import get_career_center

        with patch("app.modules.matching.resource_router.get_city_config", return_value=_fw_config()):
            cc = get_career_center()
            assert "Workforce Solutions" in cc.name
            assert "Fort Worth" in cc.address

    def test_fw_barrier_actions_mention_trinity_metro(self):
        from app.modules.matching.resource_router import get_barrier_actions
        from app.modules.matching.types import BarrierType

        with patch("app.modules.matching.resource_router.get_city_config", return_value=_fw_config()):
            actions = get_barrier_actions()
            transport = " ".join(actions[BarrierType.TRANSPORTATION])
            assert "Trinity Metro" in transport


class TestFortWorthAIIntegration:
    def test_fw_prompt_mentions_fort_worth(self):
        from app.ai.prompt_router import get_system_prompt

        with patch("app.ai.prompt_router.get_city_config", return_value=_fw_config()):
            prompt = get_system_prompt()
            assert "Fort Worth" in prompt
            assert "Trinity Metro" in prompt
            assert "Lockheed Martin" in prompt or "Bell" in prompt


class TestMontgomeryBackwardCompatibility:
    """Verify Montgomery (AL) still works correctly."""

    def test_al_benefits_still_has_all_kids(self):
        from app.modules.benefits.router import get_program_checks

        with patch("app.modules.benefits.router.get_city_config", return_value=_al_config()):
            checks = get_program_checks()
            assert "ALL_Kids" in checks
            assert "LIHEAP" in checks
            assert "CHIP" not in checks
            assert "CEAP" not in checks

    def test_al_expungement_still_works(self):
        from app.modules.criminal.router import check_record_clearing
        from app.modules.criminal.record_profile import RecordProfile, RecordType, ChargeCategory
        from app.modules.criminal.expungement import ExpungementResult

        profile = RecordProfile(
            record_types=[RecordType.ARREST_ONLY],
            charge_categories=[ChargeCategory.OTHER],
        )
        with patch("app.modules.criminal.router.get_city_config", return_value=_al_config()):
            result = check_record_clearing(profile)
            assert isinstance(result, ExpungementResult)

    def test_al_career_center_still_works(self):
        from app.modules.matching.resource_router import get_career_center

        with patch("app.modules.matching.resource_router.get_city_config", return_value=_al_config()):
            cc = get_career_center()
            assert "Montgomery" in cc.name

    def test_al_prompt_still_works(self):
        from app.ai.prompt_router import get_system_prompt

        with patch("app.ai.prompt_router.get_city_config", return_value=_al_config()):
            prompt = get_system_prompt()
            assert "Montgomery" in prompt
            assert "M-Transit" in prompt

"""Edge-case tests for prompt_router and benefits router thresholds.

Covers:
- get_system_prompt and get_user_prompt_template for both cities
- Verifies no content leakage between cities
- get_thresholds and get_sum_program_benefits router paths
"""

import pytest
from unittest.mock import patch
from app.cities.config import CityConfig


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


class TestPromptRouter:
    """AI prompt routing for both cities."""

    def test_fort_worth_system_prompt_content(self):
        from app.ai.prompt_router import get_system_prompt

        with patch("app.ai.prompt_router.get_city_config", return_value=_mock_tx()):
            prompt = get_system_prompt()
            assert "Fort Worth" in prompt
            assert "Trinity Metro" in prompt
            assert "Workforce Solutions" in prompt
            assert "Tarrant County" in prompt
            assert "Lockheed Martin" in prompt

    def test_montgomery_system_prompt_content(self):
        from app.ai.prompt_router import get_system_prompt

        with patch("app.ai.prompt_router.get_city_config", return_value=_mock_al()):
            prompt = get_system_prompt()
            assert "Montgomery" in prompt
            assert "M-Transit" in prompt
            assert "Alabama Career Center" in prompt
            assert "Hyundai" in prompt

    def test_fort_worth_user_template(self):
        from app.ai.prompt_router import get_user_prompt_template

        with patch("app.ai.prompt_router.get_city_config", return_value=_mock_tx()):
            template = get_user_prompt_template()
            assert "Fort Worth" in template
            assert "{barriers}" in template
            assert "{qualifications}" in template

    def test_montgomery_user_template(self):
        from app.ai.prompt_router import get_user_prompt_template

        with patch("app.ai.prompt_router.get_city_config", return_value=_mock_al()):
            template = get_user_prompt_template()
            assert "Montgomery" in template
            assert "{barriers}" in template

    def test_system_prompt_shared_suffix(self):
        """Both cities should include the shared suffix with security rules."""
        from app.ai.prompt_router import get_system_prompt

        with patch("app.ai.prompt_router.get_city_config", return_value=_mock_tx()):
            tx_prompt = get_system_prompt()
        with patch("app.ai.prompt_router.get_city_config", return_value=_mock_al()):
            al_prompt = get_system_prompt()
        # Both should contain security warning
        assert "untrusted user-supplied data" in tx_prompt
        assert "untrusted user-supplied data" in al_prompt

    def test_no_cross_city_leakage_in_system_prompt(self):
        """Fort Worth prompt should not mention AL-specific entities."""
        from app.ai.prompt_router import get_system_prompt

        with patch("app.ai.prompt_router.get_city_config", return_value=_mock_tx()):
            prompt = get_system_prompt()
            # Fort Worth should not mention AL career center or M-Transit
            pre_security = prompt.split("Security")[0]
            assert "Alabama Career Center" not in pre_security
            assert "M-Transit" not in pre_security

    def test_no_cross_city_leakage_in_user_template(self):
        """Montgomery template should not mention Fort Worth."""
        from app.ai.prompt_router import get_user_prompt_template

        with patch("app.ai.prompt_router.get_city_config", return_value=_mock_al()):
            template = get_user_prompt_template()
            assert "Fort Worth" not in template


class TestBenefitsRouterThresholds:
    """Router thresholds for both cities."""

    def test_tx_thresholds_have_ami(self):
        from app.modules.benefits.router import get_thresholds

        with patch("app.modules.benefits.router.get_city_config", return_value=_mock_tx()):
            t = get_thresholds()
            # TX AMI for hs=4 should be ~$78K (Fort Worth)
            assert t["AMI"][4] > 70000
            assert t["CHILD_HEALTH_PROGRAM"] == "CHIP"
            assert t["ENERGY_PROGRAM"] == "CEAP"

    def test_al_thresholds_have_ami(self):
        from app.modules.benefits.router import get_thresholds

        with patch("app.modules.benefits.router.get_city_config", return_value=_mock_al()):
            t = get_thresholds()
            # AL AMI for hs=4 should be ~$60K (Montgomery)
            assert t["AMI"][4] < 70000
            assert t["CHILD_HEALTH_PROGRAM"] == "ALL_Kids"
            assert t["ENERGY_PROGRAM"] == "LIHEAP"

    def test_tx_has_fica_rate(self):
        from app.modules.benefits.router import get_thresholds

        with patch("app.modules.benefits.router.get_city_config", return_value=_mock_tx()):
            t = get_thresholds()
            assert 0 < t["FICA_RATE"] < 0.15
            assert len(t["TAX_BRACKETS"]) > 0

    def test_tx_sum_program_benefits(self):
        """TX sum_program_benefits should use TX calculators."""
        from app.modules.benefits.router import get_sum_program_benefits
        from app.modules.benefits.types import BenefitsProfile

        with patch("app.modules.benefits.router.get_city_config", return_value=_mock_tx()):
            fn = get_sum_program_benefits()
            profile = BenefitsProfile(
                household_size=3, current_monthly_income=800,
                enrolled_programs=["SNAP", "CEAP"], state="TX",
            )
            result = fn(10000.0, profile)
            assert result > 0

    def test_al_sum_program_benefits(self):
        """AL sum_program_benefits should use AL calculators."""
        from app.modules.benefits.router import get_sum_program_benefits
        from app.modules.benefits.types import BenefitsProfile

        with patch("app.modules.benefits.router.get_city_config", return_value=_mock_al()):
            fn = get_sum_program_benefits()
            profile = BenefitsProfile(
                household_size=3, current_monthly_income=800,
                enrolled_programs=["SNAP", "LIHEAP"], state="AL",
            )
            result = fn(10000.0, profile)
            assert result > 0

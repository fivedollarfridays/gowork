"""Tests for city-aware AI prompts."""

from unittest.mock import patch
from app.cities.config import CityConfig


def _al_config():
    return CityConfig(
        name="Montgomery", state="AL", location="Montgomery, AL",
        zip_ranges=["36101-36120"], job_adapters=["brightdata"],
        data_dir="data/cities/montgomery",
    )


def _tx_config():
    return CityConfig(
        name="Fort Worth", state="TX", location="Fort Worth, TX",
        zip_ranges=["76101-76199"], job_adapters=["twc"],
        data_dir="data/cities/fort-worth",
    )


class TestCityPromptRouter:
    def test_montgomery_system_prompt_mentions_montgomery(self):
        from app.ai.prompt_router import get_system_prompt

        with patch("app.ai.prompt_router.get_city_config", return_value=_al_config()):
            prompt = get_system_prompt()
            assert "Montgomery" in prompt
            assert "M-Transit" in prompt

    def test_fort_worth_system_prompt_mentions_fort_worth(self):
        from app.ai.prompt_router import get_system_prompt

        with patch("app.ai.prompt_router.get_city_config", return_value=_tx_config()):
            prompt = get_system_prompt()
            assert "Fort Worth" in prompt
            assert "Trinity Metro" in prompt

    def test_montgomery_user_prompt_mentions_montgomery(self):
        from app.ai.prompt_router import get_user_prompt_template

        with patch("app.ai.prompt_router.get_city_config", return_value=_al_config()):
            template = get_user_prompt_template()
            assert "Montgomery" in template

    def test_fort_worth_user_prompt_mentions_fort_worth(self):
        from app.ai.prompt_router import get_user_prompt_template

        with patch("app.ai.prompt_router.get_city_config", return_value=_tx_config()):
            template = get_user_prompt_template()
            assert "Fort Worth" in template

    def test_fort_worth_prompt_has_local_employers(self):
        from app.ai.prompt_router import get_system_prompt

        with patch("app.ai.prompt_router.get_city_config", return_value=_tx_config()):
            prompt = get_system_prompt()
            assert "Lockheed Martin" in prompt or "Bell" in prompt or "BNSF" in prompt

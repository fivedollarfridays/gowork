"""Verify no Montgomery/Alabama leaks in shared production code.

Ensures all city-specific references go through routers or are in
city-specific modules (alabama/, texas/, prompt_router, etc.).
"""

import ast
from pathlib import Path

import pytest
from unittest.mock import patch

from app.cities.config import CityConfig


def _mock_tx():
    return CityConfig(
        name="Fort Worth", state="TX", location="Fort Worth, TX",
        zip_ranges=["76101-76199"], job_adapters=["twc"],
        data_dir="data/cities/fort-worth",
    )


# Directories/path segments that are allowed to contain city-specific data
_ALLOWED_SEGMENTS = {
    "alabama", "montgomery", "texas", "fort_worth",
    "__pycache__", "test", "tests", "seed", "data",
}

# Files that are city-aware routers or city-specific data
_ALLOWED_FILES = {
    "prompt_router.py", "router.py", "geo_router.py", "resource_router.py",
    "config.py", "thresholds.py", "eligibility_checks.py",
    "application_data.py", "program_calculators.py",
    "cliff_calculator.py", "eligibility_screener.py",
    "pvs_scorer.py", "salary_parser.py", "cliff_navigator.py",
    "scoring.py", "affinity.py", "eligibility.py",
    "cache.py", "salary_embed.py",
}


def _is_allowed_path(path: Path) -> bool:
    """Check if the file is in an allowed path."""
    parts = set(p.lower() for p in path.parts)
    if parts & _ALLOWED_SEGMENTS:
        return True
    if path.name in _ALLOWED_FILES:
        return True
    # Allow files in benefits/ module (they ARE the Alabama data)
    if "benefits" in parts:
        return True
    # Allow integrations (contain city-specific crawling logic)
    if "integrations" in parts:
        return True
    return False


class TestNoHardcodedMontgomeryInRouteHandlers:
    """Verify no hardcoded Montgomery/Alabama references in route handlers."""

    def test_no_36104_in_route_files(self):
        """Route files must not contain hardcoded ZIP 36104."""
        routes_dir = Path("app/routes")
        violations = []
        for py_file in routes_dir.glob("*.py"):
            content = py_file.read_text(encoding="utf-8")
            for i, line in enumerate(content.splitlines(), 1):
                if "36104" in line and not line.strip().startswith("#"):
                    violations.append(f"{py_file}:{i}: {line.strip()}")
        assert violations == [], f"Hardcoded ZIP 36104 in routes: {violations}"

    def test_no_hardcoded_alabama_career_center_in_routes(self):
        """Route files must not reference 'Alabama Career Center' directly."""
        routes_dir = Path("app/routes")
        violations = []
        for py_file in routes_dir.glob("*.py"):
            content = py_file.read_text(encoding="utf-8")
            for i, line in enumerate(content.splitlines(), 1):
                if "Alabama Career Center" in line and not line.strip().startswith("#"):
                    violations.append(f"{py_file}:{i}: {line.strip()}")
        assert violations == [], f"Alabama Career Center in routes: {violations}"


class TestCityAwareFallbackNarrative:
    """Verify fallback narrative uses city config, not hardcoded values."""

    def test_fallback_opening_no_barriers_uses_city_name(self):
        """_fallback_opening with no barriers should reference city name."""
        from app.ai.client import _fallback_opening

        with patch("app.ai.client.get_city_config", return_value=_mock_tx()):
            result = _fallback_opening([])
            assert "Fort Worth" in result
            assert "Montgomery" not in result

    def test_fallback_next_step_no_contacts_tx(self):
        """_fallback_next_step with no contacts should use TX career center."""
        from app.ai.client import _fallback_next_step

        with patch("app.ai.client.get_city_config", return_value=_mock_tx()):
            result = _fallback_next_step([])
            assert "Workforce Solutions" in result
            assert "Alabama Career Center" not in result

    def test_fallback_actions_default_tx(self):
        """_build_fallback_actions with no actions should use TX center."""
        from app.ai.client import _build_fallback_actions

        with patch("app.ai.client.get_city_config", return_value=_mock_tx()):
            result = _build_fallback_actions([])
            assert any("Workforce Solutions" in a for a in result)
            assert not any("Alabama" in a for a in result)

    def test_fallback_next_step_with_contacts_uses_city_name(self):
        """_fallback_next_step with contacts references city name."""
        from app.ai.client import _fallback_next_step

        with patch("app.ai.client.get_city_config", return_value=_mock_tx()):
            result = _fallback_next_step(["Resource Center (817-555-1234)"])
            assert "Fort Worth" in result


class TestCityAwareMockProvider:
    """Verify mock LLM provider uses city config."""

    def test_mock_provider_tx(self):
        """MockProvider references Fort Worth when CITY=fort-worth."""
        from app.ai.providers import MockProvider

        provider = MockProvider()
        with patch("app.cities.config.get_city_config", return_value=_mock_tx()):
            result = provider.build_response("test")
            assert "Fort Worth" in result
            assert "Alabama" not in result


class TestCareerCenterFallbackZip:
    """Verify career center fallback uses city-aware ZIP."""

    def test_fallback_profile_uses_city_zip(self):
        """_build_profile_from_session uses city config ZIP, not hardcoded."""
        from app.routes.career_center import _build_profile_from_session

        with patch("app.cities.config.get_city_config", return_value=_mock_tx()):
            profile = _build_profile_from_session("test-session", [], {})
            assert profile.zip_code == "76101"
            assert profile.zip_code != "36104"


class TestPromptRouterIsUsed:
    """Verify client.py uses prompt_router, not hardcoded prompts."""

    def test_client_imports_prompt_router(self):
        """client.py should import from prompt_router, not prompts."""
        source = Path("app/ai/client.py").read_text(encoding="utf-8")
        assert "from app.ai.prompt_router import" in source
        assert "from app.ai.prompts import" not in source

    def test_prompt_router_returns_tx_system_prompt(self):
        """get_system_prompt returns TX-specific prompt for Fort Worth."""
        from app.ai.prompt_router import get_system_prompt

        with patch("app.ai.prompt_router.get_city_config", return_value=_mock_tx()):
            prompt = get_system_prompt()
            assert "Fort Worth" in prompt
            assert "Montgomery" not in prompt

    def test_prompt_router_returns_tx_user_template(self):
        """get_user_prompt_template returns TX-specific for Fort Worth."""
        from app.ai.prompt_router import get_user_prompt_template

        with patch("app.ai.prompt_router.get_city_config", return_value=_mock_tx()):
            template = get_user_prompt_template()
            assert "Fort Worth" in template
            assert "Montgomery" not in template

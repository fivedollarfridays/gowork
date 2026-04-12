"""Shared fixtures for pathway tests."""

import pytest

from app.modules.benefits.types import BenefitsProfile


@pytest.fixture(autouse=True)
def _set_city_for_pathway_tests(monkeypatch):
    """Set CITY=fort-worth for pathway tests and clear caches properly."""
    from app.cities.config import load_city_config
    from app.core.config import get_settings

    monkeypatch.setenv("CITY", "fort-worth")
    get_settings.cache_clear()
    load_city_config.cache_clear()
    yield
    get_settings.cache_clear()
    load_city_config.cache_clear()


@pytest.fixture()
def snap_profile() -> BenefitsProfile:
    """Profile enrolled in SNAP -- cliff around 130% FPL."""
    return BenefitsProfile(
        household_size=3,
        current_monthly_income=1200.0,
        enrolled_programs=["SNAP"],
        dependents_under_6=1,
        dependents_6_to_17=0,
        state="TX",
    )


@pytest.fixture()
def multi_program_profile() -> BenefitsProfile:
    """Profile enrolled in SNAP + CHIP + Childcare_Subsidy."""
    return BenefitsProfile(
        household_size=4,
        current_monthly_income=1500.0,
        enrolled_programs=["SNAP", "CHIP", "Childcare_Subsidy"],
        dependents_under_6=1,
        dependents_6_to_17=1,
        state="TX",
    )


@pytest.fixture()
def no_benefits_profile() -> BenefitsProfile:
    """Profile with no enrolled programs."""
    return BenefitsProfile(
        household_size=1,
        current_monthly_income=0.0,
        enrolled_programs=[],
        state="TX",
    )

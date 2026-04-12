"""Tests for eligibility screener city-aware routing.

Verifies that the screener uses the benefits router for checks,
application data, and disclaimer based on the active city.
"""

import pytest

from app.modules.benefits.types import BenefitsProfile


@pytest.fixture
def _fort_worth_city(monkeypatch):
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
    monkeypatch.setenv("CITY", "montgomery")
    from app.cities.config import load_city_config
    load_city_config.cache_clear()
    from app.core.config import get_settings
    get_settings.cache_clear()
    yield
    load_city_config.cache_clear()
    get_settings.cache_clear()


class TestScreenerRouting:
    @pytest.mark.usefixtures("_fort_worth_city")
    def test_fort_worth_disclaimer_mentions_hhsc(self):
        """Fort Worth screener should mention HHSC, not Alabama DHR."""
        from app.modules.benefits.eligibility_screener import (
            screen_benefits_eligibility,
        )

        profile = BenefitsProfile(
            household_size=3,
            current_monthly_income=1500,
            state="TX",
        )
        result = screen_benefits_eligibility(profile)
        assert "HHSC" in result.disclaimer or "Texas" in result.disclaimer
        assert "Alabama" not in result.disclaimer

    @pytest.mark.usefixtures("_montgomery_city")
    def test_montgomery_disclaimer_mentions_dhr(self):
        """Montgomery screener should mention Alabama DHR."""
        from app.modules.benefits.eligibility_screener import (
            screen_benefits_eligibility,
        )

        profile = BenefitsProfile(
            household_size=3,
            current_monthly_income=1500,
            state="AL",
        )
        result = screen_benefits_eligibility(profile)
        assert "Alabama" in result.disclaimer

    @pytest.mark.usefixtures("_fort_worth_city")
    def test_fort_worth_uses_tx_program_checks(self):
        """Fort Worth should use TX program checks (CHIP, not ALL_Kids)."""
        from app.modules.benefits.eligibility_screener import (
            screen_benefits_eligibility,
        )

        profile = BenefitsProfile(
            household_size=4,
            current_monthly_income=1500,
            dependents_under_6=1,
            dependents_6_to_17=1,
            state="TX",
        )
        result = screen_benefits_eligibility(profile)
        all_programs = [p.program for p in result.eligible_programs + result.ineligible_programs]
        # TX should have CHIP, not ALL_Kids
        assert "CHIP" in all_programs
        assert "ALL_Kids" not in all_programs

    @pytest.mark.usefixtures("_fort_worth_city")
    def test_fort_worth_uses_tx_application_data(self):
        """Fort Worth eligible programs should have TX application info."""
        from app.modules.benefits.eligibility_screener import (
            screen_benefits_eligibility,
        )

        profile = BenefitsProfile(
            household_size=3,
            current_monthly_income=800,
            dependents_under_6=1,
            state="TX",
        )
        result = screen_benefits_eligibility(profile)
        # At least SNAP should be eligible at $800/mo for hs=3
        snap = next((p for p in result.eligible_programs if p.program == "SNAP"), None)
        assert snap is not None
        if snap.application_info:
            assert "Texas" in snap.application_info.office_name or "HHSC" in snap.application_info.office_name

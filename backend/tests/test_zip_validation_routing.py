"""Tests for agnostic ZIP validation in AssessmentRequest.

The system accepts ZIPs from ANY configured city (Montgomery AL,
Fort Worth TX) regardless of the server's default CITY setting.
"""

import pytest


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


class TestAssessmentRequestZip:
    """AssessmentRequest should accept ZIPs for the active city."""

    @pytest.mark.usefixtures("_fort_worth_city")
    def test_fort_worth_zip_accepted(self):
        """Fort Worth ZIP 76102 should be accepted."""
        from app.modules.matching.types import AssessmentRequest

        req = AssessmentRequest(
            zip_code="76102",
            employment_status="unemployed",
            barriers={"credit": True},
            work_history="Warehouse worker for 3 years",
        )
        assert req.zip_code == "76102"

    @pytest.mark.usefixtures("_montgomery_city")
    def test_montgomery_zip_accepted(self):
        """Montgomery ZIP 36104 should be accepted."""
        from app.modules.matching.types import AssessmentRequest

        req = AssessmentRequest(
            zip_code="36104",
            employment_status="unemployed",
            barriers={"credit": True},
            work_history="Warehouse worker for 3 years",
        )
        assert req.zip_code == "36104"

    @pytest.mark.usefixtures("_fort_worth_city")
    def test_montgomery_zip_accepted_in_fort_worth(self):
        """Montgomery ZIP 36104 should be accepted (agnostic validation)."""
        from app.modules.matching.types import AssessmentRequest

        req = AssessmentRequest(
            zip_code="36104",
            employment_status="unemployed",
            barriers={"credit": True},
            work_history="Warehouse worker for 3 years",
        )
        assert req.zip_code == "36104"

    @pytest.mark.usefixtures("_montgomery_city")
    def test_fort_worth_zip_accepted_in_montgomery(self):
        """Fort Worth ZIP 76102 should be accepted (agnostic validation)."""
        from app.modules.matching.types import AssessmentRequest

        req = AssessmentRequest(
            zip_code="76102",
            employment_status="unemployed",
            barriers={"credit": True},
            work_history="Warehouse worker for 3 years",
        )
        assert req.zip_code == "76102"

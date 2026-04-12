"""Tests for city-aware ZIP validation in AssessmentRequest."""

import pytest
from pydantic import ValidationError


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
    def test_montgomery_zip_rejected_in_fort_worth(self):
        """Montgomery ZIP 36104 should be rejected when CITY=fort-worth."""
        from app.modules.matching.types import AssessmentRequest

        with pytest.raises(ValidationError):
            AssessmentRequest(
                zip_code="36104",
                employment_status="unemployed",
                barriers={"credit": True},
                work_history="Warehouse worker for 3 years",
            )

    @pytest.mark.usefixtures("_montgomery_city")
    def test_fort_worth_zip_rejected_in_montgomery(self):
        """Fort Worth ZIP 76102 should be rejected when CITY=montgomery."""
        from app.modules.matching.types import AssessmentRequest

        with pytest.raises(ValidationError):
            AssessmentRequest(
                zip_code="76102",
                employment_status="unemployed",
                barriers={"credit": True},
                work_history="Warehouse worker for 3 years",
            )

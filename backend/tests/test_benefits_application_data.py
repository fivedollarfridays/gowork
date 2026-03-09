"""Tests for benefits program application data and screener integration."""

from app.modules.benefits.application_data import APPLICATION_DATA, get_application_info
from app.modules.benefits.eligibility_screener import screen_benefits_eligibility
from app.modules.benefits.types import BenefitsProfile


def _profile(**overrides) -> BenefitsProfile:
    defaults = {
        "household_size": 3,
        "current_monthly_income": 0,
        "enrolled_programs": [],
        "dependents_under_6": 0,
        "dependents_6_to_17": 0,
    }
    defaults.update(overrides)
    return BenefitsProfile(**defaults)


def _find_program(result, name: str):
    for p in result.eligible_programs + result.ineligible_programs:
        if p.program == name:
            return p
    raise ValueError(f"Program {name} not found in result")


class TestApplicationDataCompleteness:
    def test_all_seven_programs_have_data(self):
        expected = {
            "SNAP", "TANF", "Medicaid", "ALL_Kids",
            "Childcare_Subsidy", "Section_8", "LIHEAP",
        }
        assert set(APPLICATION_DATA.keys()) == expected

    def test_each_program_has_url(self):
        for name, info in APPLICATION_DATA.items():
            assert info.application_url, f"{name} missing application_url"

    def test_each_program_has_steps(self):
        for name, info in APPLICATION_DATA.items():
            assert len(info.application_steps) > 0, f"{name} has no steps"

    def test_each_program_has_required_documents(self):
        for name, info in APPLICATION_DATA.items():
            assert len(info.required_documents) > 0, f"{name} has no docs"

    def test_each_program_has_office_contact(self):
        for name, info in APPLICATION_DATA.items():
            assert info.office_name, f"{name} missing office_name"
            assert info.office_phone, f"{name} missing office_phone"

    def test_each_program_has_processing_time(self):
        for name, info in APPLICATION_DATA.items():
            assert info.processing_time, f"{name} missing processing_time"

    def test_section_8_mentions_waitlist(self):
        s8 = APPLICATION_DATA["Section_8"]
        all_text = " ".join(s8.application_steps).lower()
        assert "wait" in all_text or "wait" in s8.processing_time.lower()

    def test_liheap_mentions_seasonal(self):
        liheap = APPLICATION_DATA["LIHEAP"]
        all_text = " ".join(liheap.application_steps).lower() + liheap.processing_time.lower()
        assert "season" in all_text or "oct" in all_text or "heating" in all_text

    def test_get_application_info_returns_data(self):
        info = get_application_info("SNAP")
        assert info is not None
        assert info.application_url

    def test_get_application_info_returns_none_for_unknown(self):
        assert get_application_info("NONEXISTENT") is None


class TestScreenerIncludesApplicationInfo:
    def test_eligible_programs_have_application_info(self):
        result = screen_benefits_eligibility(_profile(current_monthly_income=0))
        for p in result.eligible_programs:
            assert p.application_info is not None, (
                f"{p.program} missing application_info"
            )

    def test_ineligible_programs_have_no_application_info(self):
        result = screen_benefits_eligibility(
            _profile(current_monthly_income=5000),
        )
        for p in result.ineligible_programs:
            assert p.application_info is None, (
                f"{p.program} should not have application_info"
            )

    def test_application_info_has_correct_program(self):
        result = screen_benefits_eligibility(_profile(current_monthly_income=0))
        snap = _find_program(result, "SNAP")
        assert snap.application_info is not None
        assert snap.application_info.application_url

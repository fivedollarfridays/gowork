"""Tests for WIOA eligibility screener."""

import pytest

from app.modules.matching.wioa_screener import (
    WIOAEligibility,
    has_expired_certification,
    screen_wioa_eligibility,
)
from app.modules.matching.types import (
    BarrierType,
    BarrierSeverity,
    EmploymentStatus,
    UserProfile,
)


def _profile(
    barriers: list[BarrierType] | None = None,
    work_history: str = "",
) -> UserProfile:
    """Build a minimal UserProfile for testing."""
    b = barriers or []
    return UserProfile(
        session_id="s-1",
        zip_code="36104",
        employment_status=EmploymentStatus.UNEMPLOYED,
        barrier_count=len(b),
        primary_barriers=b,
        barrier_severity=BarrierSeverity.LOW if len(b) <= 1 else BarrierSeverity.MEDIUM,
        needs_credit_assessment=BarrierType.CREDIT in b,
        transit_dependent=BarrierType.TRANSPORTATION in b,
        schedule_type="daytime",
        work_history=work_history,
        target_industries=[],
    )


class TestWIOAEligibilityModel:
    def test_all_fields_present(self):
        """WIOAEligibility has all 6 required fields."""
        elig = WIOAEligibility(
            adult_program=True,
            adult_reasons=["credit"],
            supportive_services=False,
            ita_training=False,
            dislocated_worker="needs_verification",
            confidence="likely",
        )
        assert elig.adult_program is True
        assert elig.adult_reasons == ["credit"]
        assert elig.supportive_services is False
        assert elig.ita_training is False
        assert elig.dislocated_worker == "needs_verification"
        assert elig.confidence == "likely"


class TestHasExpiredCertification:
    def test_cna_detected(self):
        assert has_expired_certification("Former CNA, license lapsed") is True

    def test_cdl_detected(self):
        assert has_expired_certification("Had CDL class B") is True

    def test_lpn_detected(self):
        assert has_expired_certification("LPN certification expired") is True

    def test_case_insensitive(self):
        assert has_expired_certification("used to be a cna") is True

    def test_no_cert_returns_false(self):
        assert has_expired_certification("warehouse worker for 5 years") is False

    def test_empty_string(self):
        assert has_expired_certification("") is False


class TestScreenWIOAEligibility:
    def test_credit_barrier_qualifies_adult(self):
        result = screen_wioa_eligibility(_profile([BarrierType.CREDIT]))
        assert result.adult_program is True
        assert "credit" in result.adult_reasons

    def test_transportation_barrier_qualifies_adult(self):
        result = screen_wioa_eligibility(_profile([BarrierType.TRANSPORTATION]))
        assert result.adult_program is True
        assert "transportation" in result.adult_reasons

    def test_childcare_barrier_qualifies_adult(self):
        result = screen_wioa_eligibility(_profile([BarrierType.CHILDCARE]))
        assert result.adult_program is True
        assert "childcare" in result.adult_reasons

    def test_criminal_record_qualifies_adult(self):
        result = screen_wioa_eligibility(_profile([BarrierType.CRIMINAL_RECORD]))
        assert result.adult_program is True
        assert "criminal_record" in result.adult_reasons

    def test_no_qualifying_barriers_not_eligible(self):
        result = screen_wioa_eligibility(_profile([BarrierType.HOUSING]))
        assert result.adult_program is False
        assert result.adult_reasons == []

    def test_empty_barriers_not_eligible(self):
        result = screen_wioa_eligibility(_profile([]))
        assert result.adult_program is False

    def test_multiple_barriers_all_listed(self):
        result = screen_wioa_eligibility(
            _profile([BarrierType.CREDIT, BarrierType.CHILDCARE])
        )
        assert result.adult_program is True
        assert "credit" in result.adult_reasons
        assert "childcare" in result.adult_reasons

    def test_supportive_services_with_transport(self):
        result = screen_wioa_eligibility(_profile([BarrierType.TRANSPORTATION]))
        assert result.supportive_services is True

    def test_supportive_services_with_childcare(self):
        result = screen_wioa_eligibility(_profile([BarrierType.CHILDCARE]))
        assert result.supportive_services is True

    def test_supportive_services_without_transport_or_childcare(self):
        result = screen_wioa_eligibility(_profile([BarrierType.CREDIT]))
        assert result.supportive_services is False

    def test_supportive_services_requires_adult_eligible(self):
        """Housing alone doesn't qualify for adult, so no supportive services."""
        result = screen_wioa_eligibility(_profile([BarrierType.HOUSING]))
        assert result.supportive_services is False

    def test_ita_with_cert_and_adult(self):
        result = screen_wioa_eligibility(
            _profile([BarrierType.CREDIT], work_history="Former CNA")
        )
        assert result.ita_training is True

    def test_ita_without_cert(self):
        result = screen_wioa_eligibility(
            _profile([BarrierType.CREDIT], work_history="warehouse")
        )
        assert result.ita_training is False

    def test_ita_without_adult_eligible(self):
        result = screen_wioa_eligibility(
            _profile([BarrierType.HOUSING], work_history="Former CNA")
        )
        assert result.ita_training is False

    def test_dislocated_worker_always_needs_verification(self):
        result = screen_wioa_eligibility(_profile([BarrierType.CREDIT]))
        assert result.dislocated_worker == "needs_verification"

    def test_confidence_always_likely(self):
        result = screen_wioa_eligibility(_profile([]))
        assert result.confidence == "likely"

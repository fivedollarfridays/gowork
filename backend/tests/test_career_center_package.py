"""Tests for Career Center Package assembler."""

import pytest

from app.modules.matching.career_center_package import (
    CAREER_CENTER,
    CareerCenterInfo,
    CareerCenterPackage,
    CreditPathway,
    DocumentChecklistItem,
    ResidentActionPlan,
    StaffSummary,
    assemble_package,
)
from app.modules.matching.types import (
    BarrierCard,
    BarrierSeverity,
    BarrierType,
    EmploymentStatus,
    ReEntryPlan,
    UserProfile,
)
from app.modules.matching.types import WIOAEligibility
from app.modules.credit.types import CreditAssessmentResult


def _profile(
    barriers: list[BarrierType] | None = None,
    work_history: str = "",
) -> UserProfile:
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


def _plan(barriers: list[BarrierType] | None = None) -> ReEntryPlan:
    b = barriers or []
    cards = [
        BarrierCard(
            type=bt,
            severity=BarrierSeverity.MEDIUM,
            title=f"{bt.value} barrier",
            actions=[f"Fix {bt.value}"],
        )
        for bt in b
    ]
    return ReEntryPlan(
        plan_id="p-1",
        session_id="s-1",
        barriers=cards,
        job_matches=[],
        immediate_next_steps=["Visit Career Center"],
    )


def _wioa(adult: bool = True, reasons: list[str] | None = None) -> WIOAEligibility:
    return WIOAEligibility(
        adult_program=adult,
        adult_reasons=reasons or [],
        supportive_services=False,
        ita_training=False,
        dislocated_worker="needs_verification",
        confidence="likely",
    )


def _credit_result() -> CreditAssessmentResult:
    return CreditAssessmentResult(
        barrier_severity="high",
        barrier_details=[],
        readiness={"score": 45, "fico_score": 580, "score_band": "fair", "factors": {}},
        thresholds=[],
        dispute_pathway={
            "steps": [{"step_number": 1, "action": "Get report"}],
            "total_estimated_days": 90,
            "statutes_cited": [],
            "legal_theories": [],
        },
        eligibility=[],
        disclaimer="For info only.",
    )


class TestCareerCenterInfo:
    def test_hardcoded_values(self):
        assert CAREER_CENTER.name == "Montgomery Career Center"
        assert CAREER_CENTER.phone == "334-286-1746"
        assert "Montgomery" in CAREER_CENTER.address
        assert "Mon-Fri" in CAREER_CENTER.hours
        assert "Route" in CAREER_CENTER.transit_route


class TestAssemblePackage:
    def test_returns_complete_package(self):
        pkg = assemble_package(
            _profile([BarrierType.CREDIT]),
            _plan([BarrierType.CREDIT]),
            _wioa(True, ["credit"]),
        )
        assert isinstance(pkg, CareerCenterPackage)
        assert isinstance(pkg.staff_summary, StaffSummary)
        assert isinstance(pkg.resident_plan, ResidentActionPlan)
        assert pkg.generated_at is not None

    def test_staff_summary_has_barriers(self):
        pkg = assemble_package(
            _profile([BarrierType.CREDIT, BarrierType.TRANSPORTATION]),
            _plan([BarrierType.CREDIT, BarrierType.TRANSPORTATION]),
            _wioa(True, ["credit", "transportation"]),
        )
        assert "credit" in pkg.staff_summary.barrier_profile
        assert "transportation" in pkg.staff_summary.barrier_profile

    def test_staff_summary_has_wioa(self):
        pkg = assemble_package(
            _profile([BarrierType.CREDIT]),
            _plan([BarrierType.CREDIT]),
            _wioa(True, ["credit"]),
        )
        assert pkg.staff_summary.wioa_eligibility is not None

    def test_staff_summary_has_next_steps(self):
        pkg = assemble_package(
            _profile([BarrierType.CREDIT]),
            _plan([BarrierType.CREDIT]),
            _wioa(True, ["credit"]),
        )
        assert len(pkg.staff_summary.staff_next_steps) > 0

    def test_base_docs_always_present(self):
        pkg = assemble_package(
            _profile([BarrierType.HOUSING]),
            _plan([BarrierType.HOUSING]),
            _wioa(False),
        )
        labels = [item.label for item in pkg.resident_plan.document_checklist]
        assert any("ID" in label for label in labels)
        assert any("Social Security" in label for label in labels)

    def test_childcare_adds_birth_certs(self):
        pkg = assemble_package(
            _profile([BarrierType.CHILDCARE]),
            _plan([BarrierType.CHILDCARE]),
            _wioa(True, ["childcare"]),
        )
        labels = [item.label for item in pkg.resident_plan.document_checklist]
        assert any("birth cert" in label.lower() for label in labels)

    def test_what_to_say_references_wioa(self):
        pkg = assemble_package(
            _profile([BarrierType.CREDIT]),
            _plan([BarrierType.CREDIT]),
            _wioa(True, ["credit"]),
        )
        assert any("WIOA" in line for line in pkg.resident_plan.what_to_say)

    def test_what_to_say_no_wioa_when_ineligible(self):
        pkg = assemble_package(
            _profile([BarrierType.HOUSING]),
            _plan([BarrierType.HOUSING]),
            _wioa(False),
        )
        assert not any("WIOA" in line for line in pkg.resident_plan.what_to_say)

    def test_career_center_info_attached(self):
        pkg = assemble_package(
            _profile([BarrierType.CREDIT]),
            _plan([BarrierType.CREDIT]),
            _wioa(True, ["credit"]),
        )
        assert pkg.resident_plan.career_center.name == "Montgomery Career Center"

    def test_credit_pathway_present_with_credit_barrier(self):
        pkg = assemble_package(
            _profile([BarrierType.CREDIT]),
            _plan([BarrierType.CREDIT]),
            _wioa(True, ["credit"]),
            credit_result=_credit_result(),
        )
        assert pkg.credit_pathway is not None
        assert len(pkg.credit_pathway.dispute_steps) > 0

    def test_credit_pathway_absent_without_credit_barrier(self):
        pkg = assemble_package(
            _profile([BarrierType.TRANSPORTATION]),
            _plan([BarrierType.TRANSPORTATION]),
            _wioa(True, ["transportation"]),
        )
        assert pkg.credit_pathway is None

    def test_credit_pathway_absent_without_credit_result(self):
        pkg = assemble_package(
            _profile([BarrierType.CREDIT]),
            _plan([BarrierType.CREDIT]),
            _wioa(True, ["credit"]),
        )
        assert pkg.credit_pathway is None

    def test_model_dump_serializes(self):
        pkg = assemble_package(
            _profile([BarrierType.CREDIT]),
            _plan([BarrierType.CREDIT]),
            _wioa(True, ["credit"]),
            credit_result=_credit_result(),
        )
        data = pkg.model_dump()
        assert "staff_summary" in data
        assert "resident_plan" in data
        assert "credit_pathway" in data

    def test_multi_barrier_profile(self):
        """Maria persona: credit + transportation + childcare."""
        barriers = [BarrierType.CREDIT, BarrierType.TRANSPORTATION, BarrierType.CHILDCARE]
        pkg = assemble_package(
            _profile(barriers),
            _plan(barriers),
            _wioa(True, ["credit", "transportation", "childcare"]),
            credit_result=_credit_result(),
        )
        assert pkg.staff_summary.wioa_eligibility is not None
        assert pkg.credit_pathway is not None
        labels = [item.label for item in pkg.resident_plan.document_checklist]
        assert any("birth cert" in label.lower() for label in labels)

    def test_single_barrier_no_credit(self):
        pkg = assemble_package(
            _profile([BarrierType.TRANSPORTATION]),
            _plan([BarrierType.TRANSPORTATION]),
            _wioa(True, ["transportation"]),
        )
        assert pkg.credit_pathway is None
        assert pkg.staff_summary.barrier_profile == ["transportation"]

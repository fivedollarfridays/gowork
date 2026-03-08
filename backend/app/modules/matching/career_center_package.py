"""Career Center Package assembler — combines plan, WIOA, and credit data."""

from typing import Optional

from app.modules.credit.types import CreditAssessmentResult
from app.modules.matching.career_center_types import (
    CareerCenterInfo,
    CareerCenterPackage,
    CreditPathway,
    DocumentChecklistItem,
    ResidentActionPlan,
    StaffSummary,
)
from app.modules.matching.types import BarrierType, EmploymentStatus, ReEntryPlan, UserProfile, WIOAEligibility

CAREER_CENTER = CareerCenterInfo(
    name="Montgomery Career Center",
    phone="334-286-1746",
    address="1060 East South Boulevard, Montgomery, AL 36116",
    hours="Mon-Fri 8am-5pm",
    transit_route="Route 6, East South Boulevard",
)

_BASE_DOCS = [
    DocumentChecklistItem(label="Government-issued photo ID", required=True),
    DocumentChecklistItem(label="Social Security card", required=True),
    DocumentChecklistItem(label="Resume (if available)", required=False),
    DocumentChecklistItem(label="Proof of address", required=True),
]

_FREE_CREDIT_RESOURCES = [
    "AnnualCreditReport.com: free weekly reports",
    "Consumer Financial Protection Bureau (CFPB)",
    "Alabama Legal Help: free credit dispute assistance",
]

_WHAT_TO_EXPECT = [
    "Initial intake and assessment (about 30 minutes)",
    "Review of your work history and goals",
    "Discussion of available programs and next steps",
    "Possible same-day referrals to training or services",
]


def _build_document_checklist(profile: UserProfile) -> list[DocumentChecklistItem]:
    docs = list(_BASE_DOCS)
    if BarrierType.CHILDCARE in profile.primary_barriers:
        docs.append(DocumentChecklistItem(label="Children's birth certificates", required=True))
    if profile.employment_status == EmploymentStatus.UNEMPLOYED:
        docs.append(DocumentChecklistItem(label="Proof of income or unemployment", required=True))
    return docs


def _build_what_to_say(profile: UserProfile, wioa: WIOAEligibility) -> list[str]:
    lines = ["I'm here to get help finding employment."]
    if wioa.adult_program:
        lines.append("I may qualify for the WIOA Adult program. I'd like to discuss enrollment.")
        if wioa.supportive_services:
            lines.append("I also need help with supportive services (transportation/childcare assistance).")
        if wioa.ita_training:
            lines.append("I have certifications that may need renewal. I'd like to explore Individual Training Accounts.")
    barrier_names = [b.value.replace("_", " ") for b in profile.primary_barriers]
    if barrier_names:
        lines.append(f"My main challenges are: {', '.join(barrier_names)}.")
    return lines


def _format_barrier(d: dict) -> str:
    """Format a credit barrier dict into a human-readable string."""
    desc = d.get("description", "")
    if desc:
        return desc
    severity = d.get("severity", "")
    return f"{severity} barrier" if severity else "Credit barrier"


def _format_dispute_step(s: dict) -> str:
    """Format a dispute step dict into a human-readable string."""
    action = s.get("action", "")
    desc = s.get("description", "")
    if action and desc:
        return f"{action}: {desc}"
    return action or desc or "Review your credit report"


def _build_credit_pathway(credit_result: CreditAssessmentResult) -> CreditPathway:
    blocking = [_format_barrier(d) for d in credit_result.barrier_details]
    steps = [_format_dispute_step(s) for s in credit_result.dispute_pathway.get("steps", [])]
    return CreditPathway(
        blocking=blocking, not_blocking=[], dispute_steps=steps, free_resources=_FREE_CREDIT_RESOURCES,
    )


def _build_programs(wioa: WIOAEligibility) -> list[str]:
    programs: list[str] = []
    if wioa.adult_program:
        programs.append("WIOA Adult Program")
    if wioa.supportive_services:
        programs.append("WIOA Supportive Services")
    if wioa.ita_training:
        programs.append("Individual Training Account (ITA)")
    return programs


def assemble_package(
    profile: UserProfile,
    plan: ReEntryPlan,
    wioa: WIOAEligibility,
    credit_result: Optional[CreditAssessmentResult] = None,
) -> CareerCenterPackage:
    """Assemble a career center ready package from plan + WIOA + credit data."""
    staff_steps = list(plan.immediate_next_steps)
    if wioa.adult_program:
        staff_steps.append("Screen for WIOA Adult program enrollment")

    has_credit = BarrierType.CREDIT in profile.primary_barriers
    credit_pathway = _build_credit_pathway(credit_result) if has_credit and credit_result else None

    return CareerCenterPackage(
        staff_summary=StaffSummary(
            employment_goal=f"Employment for {profile.employment_status.value} resident",
            barrier_profile=[b.value for b in profile.primary_barriers],
            wioa_eligibility=wioa if wioa.adult_program else None,
            staff_next_steps=staff_steps,
        ),
        resident_plan=ResidentActionPlan(
            document_checklist=_build_document_checklist(profile),
            work_history=profile.work_history,
            what_to_say=_build_what_to_say(profile, wioa),
            what_to_expect=_WHAT_TO_EXPECT,
            career_center=CAREER_CENTER,
            programs=_build_programs(wioa),
        ),
        credit_pathway=credit_pathway,
    )

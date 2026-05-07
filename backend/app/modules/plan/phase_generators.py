"""Per-module phase generators for the action plan timeline."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.modules.matching.resource_router import get_career_center
from app.modules.plan.generators_barriers import (  # noqa: F401 — re-export
    generate_credit_actions,
    generate_criminal_actions,
)
from app.modules.plan.types import ActionCategory, ActionItem

if TYPE_CHECKING:
    from app.modules.benefits.types import BenefitsEligibility, CliffAnalysis
    from app.modules.matching.types_wioa import WIOAEligibility


def generate_career_center_action() -> ActionItem:
    """Always-present first action: visit the Career Center. City-aware."""
    cc = get_career_center()
    return ActionItem(
        category=ActionCategory.CAREER_CENTER,
        title=f"Visit {cc.name}",
        priority=0,
        source_module="career_center",
        resource_name=cc.name,
        resource_phone=cc.phone,
        resource_address=cc.address,
    )


def generate_job_actions(strong_matches: list) -> list[ActionItem]:
    """Top 3 jobs as Week 1-2 application actions."""
    actions: list[ActionItem] = []
    for job in strong_matches[:3]:
        company = getattr(job, "company", None) or "employer"
        pay = getattr(job, "pay_range", None)
        actions.append(ActionItem(
            category=ActionCategory.JOB_APPLICATION,
            title=f"Apply to {job.title} at {company}",
            detail=f"{pay}" if pay else None,
            priority=len(actions) + 1,
            source_module="job_matching",
        ))
    return actions


def generate_benefits_actions(
    eligibility: BenefitsEligibility | None,
    enrolled_programs: list[str],
) -> list[ActionItem]:
    """Benefits enrollment actions for eligible but not-yet-enrolled programs."""
    if not eligibility:
        return []
    enrolled_set = set(enrolled_programs)
    actions: list[ActionItem] = []
    for prog in eligibility.eligible_programs:
        if prog.program in enrolled_set:
            continue
        phone = prog.application_info.office_phone if prog.application_info else None
        name = prog.application_info.office_name if prog.application_info else None
        actions.append(ActionItem(
            category=ActionCategory.BENEFITS_ENROLLMENT,
            title=f"Apply for {prog.program} benefits",
            detail=f"Est. ${prog.estimated_monthly_value:.0f}/mo",
            priority=len(actions),
            source_module="benefits_eligibility",
            resource_name=name,
            resource_phone=phone,
        ))
    return actions


def generate_wioa_actions(wioa: WIOAEligibility | None) -> list[ActionItem]:
    """WIOA enrollment action if eligible."""
    if not wioa or not wioa.adult_program:
        return []
    cc = get_career_center()
    actions = [ActionItem(
        category=ActionCategory.TRAINING,
        title="Enroll in WIOA Adult Program",
        detail="Training vouchers and supportive services available",
        priority=0,
        source_module="wioa",
        resource_name=cc.name,
        resource_phone=cc.phone,
    )]
    if wioa.ita_training:
        actions.append(ActionItem(
            category=ActionCategory.TRAINING,
            title="Apply for WIOA ITA training voucher",
            detail="Covers tuition for approved training programs",
            priority=1,
            source_module="wioa",
        ))
    return actions


_FOLLOWUP_BARRIERS_SKIP = frozenset({"credit", "criminal_record"})

_FOLLOWUP_CATEGORY_BY_BARRIER: dict[str, ActionCategory] = {
    "transportation": ActionCategory.CAREER_CENTER,
    "childcare": ActionCategory.CHILDCARE,
    "training": ActionCategory.TRAINING,
    "health": ActionCategory.CAREER_CENTER,
    "housing": ActionCategory.HOUSING,
}


def generate_barrier_followups(barriers: list) -> list[tuple[str, ActionItem]]:
    """Month 1 follow-up actions for non-credit/non-criminal barriers.

    The credit + criminal generators already produce timeline actions; the
    other barrier types (transportation, childcare, training, health,
    housing) only surface as resource cards, leaving the timeline thin
    after Week 1-2.  For each remaining primary barrier with a resource
    on the card, emit one Month-1 follow-up so the user has a concrete
    check-in scheduled instead of an empty stretch.
    """
    out: list[tuple[str, ActionItem]] = []
    for card in barriers or []:
        barrier_value = getattr(card.type, "value", str(card.type))
        if barrier_value in _FOLLOWUP_BARRIERS_SKIP:
            continue
        resources = getattr(card, "resources", None) or []
        if not resources:
            continue
        category = _FOLLOWUP_CATEGORY_BY_BARRIER.get(
            barrier_value, ActionCategory.CAREER_CENTER,
        )
        top = resources[0]
        subject = card.title.lower().rstrip()
        if subject.endswith(" support"):
            subject = subject[: -len(" support")]
        out.append(("month_1", ActionItem(
            category=category,
            title=f"Follow up with {top.name}",
            detail=f"Confirm enrollment / next step for {subject}",
            priority=len(out),
            source_module="barrier_followup",
            resource_name=top.name,
            resource_phone=getattr(top, "phone", None),
            resource_address=getattr(top, "address", None),
        )))
    return out


def generate_cliff_actions(cliff: CliffAnalysis | None) -> list[ActionItem]:
    """Benefits cliff transition plan for Month 6-12."""
    if not cliff or not cliff.cliff_points:
        return []
    worst = cliff.cliff_points[0]
    recovery = cliff.recovery_wage
    detail_parts = [f"Avoid ${worst.hourly_wage:.0f}/hr cliff ({worst.lost_program})"]
    if recovery:
        detail_parts.append(f"target ${recovery:.0f}/hr+ for net gain")
    return [ActionItem(
        category=ActionCategory.BENEFITS_ENROLLMENT,
        title="Plan benefits transition to avoid cliff",
        detail="; ".join(detail_parts),
        priority=0,
        source_module="benefits_cliff",
    )]

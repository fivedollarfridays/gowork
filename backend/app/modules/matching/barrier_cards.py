"""Barrier card construction — builds BarrierCards with eligibility annotations."""

from __future__ import annotations

from app.modules.benefits.types import BenefitsProfile
from app.modules.criminal.expungement import ExpungementEligibility, ExpungementResult
from app.modules.criminal.router import check_record_clearing
from app.modules.criminal.texas_expunction import TexasRecordClearingResult
from app.modules.matching.affinity import assign_resources
from app.modules.matching.barrier_priority import prioritize_barriers
from app.modules.matching.filters import get_certification_renewal
from app.modules.matching.resource_router import get_barrier_actions, get_career_center_step
from app.modules.matching.types import (
    BarrierCard,
    BarrierType,
    Resource,
    UserProfile,
)
from app.modules.resources.eligibility import check_eligibility

# Human-readable titles for barrier types
BARRIER_TITLES: dict[BarrierType, str] = {
    BarrierType.CREDIT: "Credit & Financial Health",
    BarrierType.TRANSPORTATION: "Transportation Access",
    BarrierType.CHILDCARE: "Childcare Support",
    BarrierType.HOUSING: "Housing Stability",
    BarrierType.HEALTH: "Health & Wellness",
    BarrierType.TRAINING: "Training & Certification",
    BarrierType.CRIMINAL_RECORD: "Record & Legal Support",
}


def normalize_expungement(
    result: ExpungementResult | TexasRecordClearingResult | None,
) -> ExpungementResult | None:
    """Normalize any record-clearing result to a single ExpungementResult.

    Texas returns a ``TexasRecordClearingResult`` wrapping two inner
    ``ExpungementResult`` objects (expunction + nondisclosure). We pick
    the most actionable one so downstream consumers (action-plan
    generator, frontend card view) see a uniform shape.

    Priority: expunction-eligible-now > nondisclosure-eligible-now
    > expunction-eligible-future > nondisclosure-eligible-future
    > expunction (as fallback).
    """
    if result is None:
        return None
    if isinstance(result, ExpungementResult):
        return result
    # TexasRecordClearingResult — pick the best inner result.
    exp = result.expunction_result
    nond = result.nondisclosure_result
    for candidate in (exp, nond):
        if candidate.eligibility == ExpungementEligibility.ELIGIBLE_NOW:
            return candidate
    for candidate in (exp, nond):
        if candidate.eligibility == ExpungementEligibility.ELIGIBLE_FUTURE:
            return candidate
    return exp  # fallback: always return expunction result


# DEPRECATED: Montgomery-specific barrier actions. Used only by resource_router
# for the Alabama code path. Fort Worth equivalent is in fort_worth_resources.py.
# Do NOT import this constant directly — use get_barrier_actions() from resource_router.
BARRIER_ACTIONS: dict[BarrierType, list[str]] = {
    BarrierType.CREDIT: [
        "Request free credit report from annualcreditreport.com",
        "Review report for errors and dispute inaccuracies",
        "Contact a local career center for credit counseling referral",
    ],
    BarrierType.TRANSPORTATION: [
        "Review M-Transit routes and schedules (Mon-Sat, ~5am-9pm)",
        "Apply for M-Transit reduced fare if income-eligible",
        "Contact career center about transportation assistance programs",
    ],
    BarrierType.CHILDCARE: [
        "Contact DHR for childcare subsidy eligibility",
        "Research childcare providers near home and potential workplaces",
        "Apply for Alabama Pre-K or Head Start if age-eligible",
    ],
    BarrierType.HOUSING: [
        "Contact Montgomery Housing Authority for assistance programs",
        "Visit local social services for emergency housing resources",
        "Gather documentation for housing applications",
    ],
    BarrierType.HEALTH: [
        "Enroll in Medicaid if income-eligible",
        "Contact community health centers for sliding-scale services",
        "Schedule wellness check and address any urgent health needs",
    ],
    BarrierType.TRAINING: [
        "Review current certifications and identify expired credentials",
        "Contact training programs for enrollment and scheduling",
        "Research financial aid and scholarship opportunities",
    ],
    BarrierType.CRIMINAL_RECORD: [
        "Request background check to understand what employers see",
        "Contact legal aid for record expungement eligibility",
        "Connect with re-entry career support programs",
    ],
}


def build_barrier_cards_and_steps(
    profile: UserProfile, resources: list[Resource],
    benefits_profile: BenefitsProfile | None = None,
) -> tuple[list[BarrierCard], list[str]]:
    """Build sorted barrier cards and immediate next steps."""
    sorted_barriers = prioritize_barriers([b.value for b in profile.primary_barriers])
    sorted_profile = profile.model_copy(
        update={"primary_barriers": [BarrierType(b) for b in sorted_barriers]},
    )
    cards = _build_cards(sorted_profile, resources)
    _annotate_eligibility(cards, benefits_profile)
    steps = _build_next_steps(cards)
    return cards, steps


def _annotate_eligibility(
    cards: list[BarrierCard],
    benefits_profile: BenefitsProfile | None,
) -> None:
    """Set eligibility_status on each resource in barrier cards."""
    from app.modules.resources.eligibility import EligibilityStatus

    for card in cards:
        for resource in card.resources:
            status = check_eligibility(resource, benefits_profile)
            resource.eligibility_status = status.value if status != EligibilityStatus.UNKNOWN else None


def _build_cards(
    profile: UserProfile, resources: list[Resource],
) -> list[BarrierCard]:
    """Create a BarrierCard for each primary barrier with affinity routing."""
    card_resources = assign_resources(set(profile.primary_barriers), resources)

    city_actions = get_barrier_actions()
    cards: list[BarrierCard] = []
    for barrier in profile.primary_barriers:
        actions = list(city_actions.get(barrier, []))
        expungement = None

        if barrier == BarrierType.TRAINING:
            cert_renewals = get_certification_renewal(profile.work_history)
            for cert in cert_renewals:
                actions.append(
                    f"Renew {cert['certification_type']}: "
                    f"Contact {cert['renewal_body']['name']} "
                    f"({cert['renewal_body'].get('phone', 'N/A')})"
                )

        if barrier == BarrierType.CRIMINAL_RECORD:
            raw_result = check_record_clearing(profile.record_profile)
            expungement = normalize_expungement(raw_result)

        cards.append(BarrierCard(
            type=barrier,
            severity=profile.barrier_severity,
            title=BARRIER_TITLES.get(barrier, barrier.value.replace("_", " ").title()),
            actions=actions,
            resources=card_resources.get(barrier, []),
            expungement=expungement,
        ))

    return cards


def _next_step_subject(title: str) -> str:
    """Strip trailing 'support' from a barrier title for use in the next-step
    template. ``BARRIER_TITLES`` already include the word (e.g. "Childcare
    Support", "Record & Legal Support") — appending it again produces
    "for childcare support support". Keep the title-cased prefix only.
    """
    lowered = title.lower().rstrip()
    if lowered.endswith(" support"):
        return lowered[: -len(" support")]
    return lowered


def _build_next_steps(cards: list[BarrierCard]) -> list[str]:
    """Generate prioritized immediate next steps."""
    steps: list[str] = [get_career_center_step()]

    for card in cards[:3]:
        if card.resources:
            top = card.resources[0]
            contact = f" ({top.phone})" if top.phone else ""
            subject = _next_step_subject(card.title)
            steps.append(f"Contact {top.name}{contact} for {subject} support")
        elif card.actions:
            steps.append(card.actions[0])

    return steps

"""Barrier card construction — builds BarrierCards with eligibility annotations."""

from app.modules.benefits.types import BenefitsProfile
from app.modules.matching.affinity import CAREER_CENTER_STEP, assign_resources
from app.modules.matching.barrier_priority import prioritize_barriers
from app.modules.matching.filters import get_certification_renewal
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

# Default action steps per barrier type
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
    steps = _build_next_steps(profile, cards)
    return cards, steps


def _annotate_eligibility(
    cards: list[BarrierCard],
    benefits_profile: BenefitsProfile | None,
) -> None:
    """Set eligibility_status on each resource in barrier cards."""
    for card in cards:
        for i, resource in enumerate(card.resources):
            status = check_eligibility(resource, benefits_profile)
            card.resources[i] = resource.model_copy(
                update={"eligibility_status": status.value},
            )


def _build_cards(
    profile: UserProfile, resources: list[Resource],
) -> list[BarrierCard]:
    """Create a BarrierCard for each primary barrier with affinity routing."""
    card_resources = assign_resources(set(profile.primary_barriers), resources)

    cards: list[BarrierCard] = []
    for barrier in profile.primary_barriers:
        actions = list(BARRIER_ACTIONS.get(barrier, []))

        if barrier == BarrierType.TRAINING:
            cert_renewals = get_certification_renewal(profile.work_history)
            for cert in cert_renewals:
                actions.append(
                    f"Renew {cert['certification_type']}: "
                    f"Contact {cert['renewal_body']['name']} "
                    f"({cert['renewal_body'].get('phone', 'N/A')})"
                )

        cards.append(BarrierCard(
            type=barrier,
            severity=profile.barrier_severity,
            title=BARRIER_TITLES.get(barrier, barrier.value.replace("_", " ").title()),
            actions=actions,
            resources=card_resources.get(barrier, []),
        ))

    return cards


def _build_next_steps(
    profile: UserProfile, cards: list[BarrierCard],
) -> list[str]:
    """Generate prioritized immediate next steps."""
    steps: list[str] = [CAREER_CENTER_STEP]

    for card in cards[:3]:
        if card.resources:
            top = card.resources[0]
            contact = f" ({top.phone})" if top.phone else ""
            steps.append(f"Contact {top.name}{contact} for {card.title.lower()} support")
        elif card.actions:
            steps.append(card.actions[0])

    return steps

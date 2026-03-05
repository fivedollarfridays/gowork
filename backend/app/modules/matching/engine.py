"""Matching engine core — takes a UserProfile and returns ranked resources."""

import uuid

from app.core.queries import get_resources_by_category
from app.modules.matching.filters import get_certification_renewal
from app.modules.matching.scoring import BARRIER_CATEGORY_MAP, rank_resources
from app.modules.matching.types import (
    BarrierCard,
    BarrierType,
    ReEntryPlan,
    Resource,
    UserProfile,
)

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


async def query_resources_for_barriers(
    barriers: list[BarrierType], db_session,
) -> list[Resource]:
    """Query Montgomery data for resources matching the user's barrier types."""
    seen_ids: set[int] = set()
    results: list[Resource] = []

    categories: set[str] = set()
    for barrier in barriers:
        categories.update(BARRIER_CATEGORY_MAP.get(barrier, set()))

    for category in sorted(categories):
        rows = await get_resources_by_category(db_session, category)
        for row in rows:
            if row["id"] not in seen_ids:
                seen_ids.add(row["id"])
                results.append(Resource(**{
                    k: row[k] for k in Resource.model_fields if k in row
                }))

    return results


async def generate_plan(
    profile: UserProfile, db_session,
) -> ReEntryPlan:
    """Orchestrate the full matching pipeline."""
    resources = await query_resources_for_barriers(
        profile.primary_barriers, db_session,
    )

    # Score and rank resources by relevance to user profile
    resources = rank_resources(resources, profile)

    # Build barrier cards
    barrier_cards = _build_barrier_cards(profile, resources)

    # Build immediate next steps
    next_steps = _build_next_steps(profile, barrier_cards)

    return ReEntryPlan(
        plan_id=str(uuid.uuid4()),
        session_id=profile.session_id,
        barriers=barrier_cards,
        job_matches=[],
        immediate_next_steps=next_steps,
    )


def _build_barrier_cards(
    profile: UserProfile, resources: list[Resource],
) -> list[BarrierCard]:
    """Create a BarrierCard for each primary barrier."""
    cards: list[BarrierCard] = []

    for barrier in profile.primary_barriers:
        matching_categories = BARRIER_CATEGORY_MAP.get(barrier, set())
        matched = [r for r in resources if r.category in matching_categories]

        actions = list(BARRIER_ACTIONS.get(barrier, []))

        # Add certification renewal steps if training barrier
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
            resources=matched,
        ))

    return cards


def _build_next_steps(
    profile: UserProfile, cards: list[BarrierCard],
) -> list[str]:
    """Generate prioritized immediate next steps."""
    steps: list[str] = []

    for card in cards[:3]:
        if card.resources:
            top = card.resources[0]
            contact = f" ({top.phone})" if top.phone else ""
            steps.append(f"Contact {top.name}{contact} for {card.title.lower()} support")
        elif card.actions:
            steps.append(card.actions[0])

    if not steps:
        steps.append("Visit a local career center for personalized guidance")

    return steps

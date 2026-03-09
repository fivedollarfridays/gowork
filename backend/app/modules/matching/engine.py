"""Matching engine core — takes a UserProfile and returns ranked resources."""

import json
import uuid

from app.core.queries import get_all_transit_stops, get_resources_by_categories
from app.modules.benefits.types import BenefitsProfile
from app.modules.matching.affinity import (
    CAREER_CENTER_STEP,
    assign_resources,
)
from app.modules.matching.barrier_priority import prioritize_barriers
from app.modules.matching.filters import get_certification_renewal
from app.modules.matching.job_matcher import match_jobs
from app.modules.matching.job_readiness import assess_job_readiness
from app.modules.matching.resume_parser import parse_resume
from app.modules.matching.scoring import (
    BARRIER_CATEGORY_MAP,
    haversine_miles,
    rank_resources,
)
from app.modules.matching.types import (
    BarrierCard,
    BarrierType,
    ReEntryPlan,
    Resource,
    ResourceHealth,
    ScoredJobMatch,
    UserProfile,
)
from app.modules.matching.wioa_screener import screen_wioa_eligibility

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
    categories: set[str] = set()
    for barrier in barriers:
        categories.update(BARRIER_CATEGORY_MAP.get(barrier, set()))

    rows = await get_resources_by_categories(db_session, categories)

    seen_ids: set[int] = set()
    results: list[Resource] = []
    for row in rows:
        if row["id"] not in seen_ids:
            # Exclude HIDDEN resources
            if row.get("health_status") == ResourceHealth.HIDDEN.value:
                continue
            seen_ids.add(row["id"])
            fields = {k: row[k] for k in Resource.model_fields if k in row}
            if isinstance(fields.get("services"), str):
                fields["services"] = json.loads(fields["services"])
            results.append(Resource(**fields))

    return results


def _compute_stop_distances(
    resources: list[Resource], stops: list[dict],
) -> dict[int, float]:
    """For each resource with coordinates, find minimum distance to any transit stop."""
    stop_coords = [(s["lat"], s["lng"]) for s in stops]
    if not stop_coords:
        return {}
    distances: dict[int, float] = {}
    for r in resources:
        if r.lat is None or r.lng is None:
            continue
        min_dist = min(
            haversine_miles(r.lat, r.lng, slat, slng)
            for slat, slng in stop_coords
        )
        distances[r.id] = min_dist
    return distances


async def _rank_with_transit(
    profile: UserProfile, resources: list[Resource], db_session,
) -> list[Resource]:
    """Rank resources, factoring in transit stop proximity for transit-dependent users."""
    stop_distances: dict[int, float] | None = None
    if profile.transit_dependent:
        stops = await get_all_transit_stops(db_session)
        if stops:
            stop_distances = _compute_stop_distances(resources, stops)
    return rank_resources(resources, profile, stop_distances=stop_distances)


def _split_legacy_buckets(
    jobs: list[ScoredJobMatch],
) -> tuple[list[ScoredJobMatch], list[ScoredJobMatch]]:
    """Split flat PVS list into legacy strong/after_repair buckets."""
    strong: list[ScoredJobMatch] = []
    after_repair: list[ScoredJobMatch] = []
    for j in jobs:
        (after_repair if j.credit_check_required == "required" else strong).append(j)
    return strong, after_repair


def _barrier_cards_and_steps(
    profile: UserProfile, resources: list[Resource],
) -> tuple[list[BarrierCard], list[str]]:
    """Build sorted barrier cards and immediate next steps."""
    sorted_barriers = prioritize_barriers([b.value for b in profile.primary_barriers])
    sorted_profile = profile.model_copy(
        update={"primary_barriers": [BarrierType(b) for b in sorted_barriers]},
    )
    cards = _build_barrier_cards(sorted_profile, resources)
    steps = _build_next_steps(profile, cards)
    return cards, steps


def _compute_benefits(
    profile: BenefitsProfile | None,
) -> tuple:  # (CliffAnalysis | None, BenefitsEligibility | None)
    """Compute cliff analysis and eligibility screening for benefits profile."""
    from app.modules.benefits.cliff_calculator import calculate_cliff_analysis
    from app.modules.benefits.eligibility_screener import screen_benefits_eligibility

    if not profile:
        return None, None
    cliff = calculate_cliff_analysis(profile) if profile.enrolled_programs else None
    eligibility = screen_benefits_eligibility(profile)
    return cliff, eligibility


async def generate_plan(
    profile: UserProfile, db_session,
    resume_text: str = "",
    credit_result: dict | None = None,
    benefits_profile: BenefitsProfile | None = None,
) -> ReEntryPlan:
    """Orchestrate the full matching pipeline."""
    resources = await query_resources_for_barriers(profile.primary_barriers, db_session)
    resources = await _rank_with_transit(profile, resources, db_session)

    ranked_jobs = await match_jobs(profile, db_session, benefits_profile=benefits_profile)
    strong, after_repair = _split_legacy_buckets(ranked_jobs)
    barrier_cards, next_steps = _barrier_cards_and_steps(profile, resources)

    parsed_resume = parse_resume(resume_text) if resume_text else None
    readiness = assess_job_readiness(profile, parsed_resume, ranked_jobs, credit_result)
    cliff, eligibility = _compute_benefits(benefits_profile)

    return ReEntryPlan(
        plan_id=str(uuid.uuid4()),
        session_id=profile.session_id,
        barriers=barrier_cards,
        strong_matches=strong,
        possible_matches=[],  # Deprecated: PVS replaces 3-bucket system
        after_repair=after_repair,
        immediate_next_steps=next_steps,
        eligible_now=[m.title for m in strong],
        eligible_after_repair=[m.title for m in after_repair],
        wioa_eligibility=screen_wioa_eligibility(profile),
        job_readiness=readiness,
        benefits_cliff_analysis=cliff,
        benefits_eligibility=eligibility,
    )


def _build_barrier_cards(
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

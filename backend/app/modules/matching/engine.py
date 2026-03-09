"""Matching engine core — takes a UserProfile and returns ranked resources."""

import json
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.queries import get_all_transit_stops, get_resources_by_categories
from app.modules.benefits.types import BenefitsProfile
from app.modules.matching import scoring, wioa_screener
from app.modules.matching.barrier_cards import build_barrier_cards_and_steps
from app.modules.matching.job_matcher import match_jobs
from app.modules.matching.job_readiness import assess_job_readiness
from app.modules.matching.resume_parser import parse_resume
from app.modules.matching.types import (
    BarrierType,
    ReEntryPlan,
    Resource,
    ScoredJobMatch,
    UserProfile,
)


async def query_resources_for_barriers(
    barriers: list[BarrierType], db_session: AsyncSession,
) -> list[Resource]:
    """Query Montgomery data for resources matching the user's barrier types."""
    categories: set[str] = set()
    for barrier in barriers:
        categories.update(scoring.BARRIER_CATEGORY_MAP.get(barrier, set()))

    rows = await get_resources_by_categories(db_session, categories)

    seen_ids: set[int] = set()
    results: list[Resource] = []
    for row in rows:
        if row["id"] not in seen_ids:
            # Exclude HIDDEN resources
            if row.get("health_status") == "hidden":
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
            scoring.haversine_miles(r.lat, r.lng, slat, slng)
            for slat, slng in stop_coords
        )
        distances[r.id] = min_dist
    return distances


async def _rank_with_transit(
    profile: UserProfile, resources: list[Resource], db_session: AsyncSession,
) -> list[Resource]:
    """Rank resources, factoring in transit stop proximity for transit-dependent users."""
    stop_distances: dict[int, float] | None = None
    if profile.transit_dependent:
        stops = await get_all_transit_stops(db_session)
        if stops:
            stop_distances = _compute_stop_distances(resources, stops)
    return scoring.rank_resources(resources, profile, stop_distances=stop_distances)


def _split_legacy_buckets(
    jobs: list[ScoredJobMatch],
) -> tuple[list[ScoredJobMatch], list[ScoredJobMatch]]:
    """Split flat PVS list into legacy strong/after_repair buckets."""
    strong: list[ScoredJobMatch] = []
    after_repair: list[ScoredJobMatch] = []
    for j in jobs:
        (after_repair if j.credit_check_required == "required" else strong).append(j)
    return strong, after_repair


def _build_action_plan(
    strong_matches: list[ScoredJobMatch],
    eligibility: "BenefitsEligibility | None",
    benefits_profile: BenefitsProfile | None,
    wioa: "WIOAEligibility | None",
    cliff: "CliffAnalysis | None",
    credit_result: dict | None,
    barriers: list,
) -> "ActionPlan":
    """Build phased action plan from all module outputs."""
    from datetime import date
    from app.modules.plan import action_plan as plan_mod

    enrolled = benefits_profile.enrolled_programs if benefits_profile else []
    return plan_mod.build_action_plan(
        strong_matches=strong_matches,
        benefits_eligibility=eligibility,
        enrolled_programs=enrolled,
        wioa_eligibility=wioa,
        cliff_analysis=cliff,
        credit_result=credit_result,
        barriers=barriers,
        assessment_date=date.today(),
    )


def _compute_benefits(
    profile: BenefitsProfile | None,
) -> "tuple[CliffAnalysis | None, BenefitsEligibility | None]":
    """Compute cliff analysis and eligibility screening for benefits profile."""
    from app.modules.benefits.cliff_calculator import calculate_cliff_analysis
    from app.modules.benefits.eligibility_screener import screen_benefits_eligibility

    if not profile:
        return None, None
    cliff = calculate_cliff_analysis(profile) if profile.enrolled_programs else None
    eligibility = screen_benefits_eligibility(profile)
    return cliff, eligibility


def _assemble_plan(
    profile: UserProfile, barrier_cards: list, strong: list[ScoredJobMatch],
    after_repair: list[ScoredJobMatch], next_steps: list,
    wioa, readiness, credit_result: dict | None, cliff, eligibility, action_plan,
) -> ReEntryPlan:
    """Build the final ReEntryPlan from all computed outputs."""
    credit_score = (
        credit_result.get("readiness", {}).get("score")
        if credit_result else None
    )
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
        wioa_eligibility=wioa,
        job_readiness=readiness,
        credit_readiness_score=credit_score,
        benefits_cliff_analysis=cliff,
        benefits_eligibility=eligibility,
        action_plan=action_plan,
    )


async def generate_plan(
    profile: UserProfile, db_session: AsyncSession,
    resume_text: str = "",
    credit_result: dict | None = None,
    benefits_profile: BenefitsProfile | None = None,
) -> ReEntryPlan:
    """Orchestrate the full matching pipeline."""
    resources = await query_resources_for_barriers(profile.primary_barriers, db_session)
    resources = await _rank_with_transit(profile, resources, db_session)

    ranked_jobs = await match_jobs(profile, db_session, benefits_profile=benefits_profile)
    strong, after_repair = _split_legacy_buckets(ranked_jobs)
    barrier_cards, next_steps = build_barrier_cards_and_steps(
        profile, resources, benefits_profile,
    )

    parsed_resume = parse_resume(resume_text) if resume_text else None
    readiness = assess_job_readiness(profile, parsed_resume, ranked_jobs, credit_result)
    cliff, eligibility = _compute_benefits(benefits_profile)
    wioa = wioa_screener.screen_wioa_eligibility(profile)
    action_plan = _build_action_plan(
        strong, eligibility, benefits_profile, wioa, cliff, credit_result, barrier_cards,
    )
    return _assemble_plan(
        profile, barrier_cards, strong, after_repair, next_steps,
        wioa, readiness, credit_result, cliff, eligibility, action_plan,
    )

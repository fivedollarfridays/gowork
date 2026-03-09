"""Job matcher: filter pipeline for personalized job matching."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.queries_jobs import get_all_job_listings
from app.modules.criminal.job_filter import filter_jobs_by_record
from app.modules.criminal.queries import get_all_employer_policies
from app.modules.matching.job_keywords import INDUSTRY_KEYWORDS, SCHEDULE_CONFLICT_KEYWORDS, SUNDAY_KEYWORDS
from app.modules.matching.job_scoring import job_search_text
from app.modules.benefits.types import BenefitsProfile
from app.modules.matching.pvs_scorer import rank_all_jobs
from app.modules.matching.transit_schedule import build_transit_info, schedule_hours_for
from app.modules.matching.types import AvailableHours, ScoredJobMatch, ScoringContext, TransitWarning, UserProfile


async def _get_stops_with_routes(db_session: AsyncSession) -> list[dict]:
    """Fetch transit stops joined with route schedule data."""
    result = await db_session.execute(text(
        "SELECT s.stop_name, s.lat, s.lng, s.route_id, "
        "r.route_number, r.route_name, r.weekday_start, r.weekday_end, "
        "r.saturday, r.sunday "
        "FROM transit_stops s JOIN transit_routes r ON s.route_id = r.id "
        "WHERE s.lat IS NOT NULL AND s.lng IS NOT NULL"
    ))
    return [dict(row._mapping) for row in result]


def _filter_by_industry(jobs: list[dict], target_industries: list[str]) -> list[dict]:
    """Annotate jobs with industry_match flag based on target industries."""
    if not target_industries:
        return [{**j, "industry_match": False} for j in jobs]

    target_keywords: set[str] = set()
    for industry in target_industries:
        target_keywords.update(INDUSTRY_KEYWORDS.get(industry, set()))

    results = []
    for job in jobs:
        searchable = job_search_text(job)
        match = any(kw in searchable for kw in target_keywords)
        results.append({**job, "industry_match": match})
    return results


def _filter_by_schedule(jobs: list[dict], available_hours: AvailableHours) -> list[dict]:
    """Annotate jobs with schedule_conflict flag."""
    if available_hours == AvailableHours.FLEXIBLE:
        return [{**j, "schedule_conflict": False} for j in jobs]

    conflict_keywords = SCHEDULE_CONFLICT_KEYWORDS.get(available_hours.value, set())
    results = []
    for job in jobs:
        desc = (job.get("description") or "").lower()
        conflict = any(kw in desc for kw in conflict_keywords)
        results.append({**job, "schedule_conflict": conflict})
    return results


def _filter_by_transit(
    jobs: list[dict], transit_dependent: bool,
    stops_with_routes: list[dict],
    schedule_type: str = "daytime",
) -> list[dict]:
    """Annotate jobs with transit_accessible, sunday_flag, and transit_info."""
    if not transit_dependent:
        return [{**j, "transit_accessible": True, "sunday_flag": False} for j in jobs]

    shift = schedule_hours_for(schedule_type)
    shift_start = shift[0] if shift else None
    shift_end = shift[1] if shift else None

    results = []
    for job in jobs:
        job_lat = job.get("lat")
        job_lng = job.get("lng")

        if job_lat is not None and job_lng is not None and stops_with_routes:
            info = build_transit_info(
                job_lat, job_lng, stops_with_routes,
                shift_start=shift_start, shift_end=shift_end,
            )
            accessible = len(info.serving_routes) > 0
            sunday_flag = any(w == TransitWarning.SUNDAY_GAP for w in info.warnings)
            results.append({
                **job,
                "transit_accessible": accessible,
                "sunday_flag": sunday_flag,
                "transit_info": info,
            })
        else:
            accessible, sunday_flag = _keyword_transit_check(job)
            results.append({
                **job, "transit_accessible": accessible, "sunday_flag": sunday_flag,
            })
    return results


def _keyword_transit_check(job: dict) -> tuple[bool, bool]:
    """Fallback: keyword-based transit check for jobs without coordinates."""
    desc = (job.get("description") or "").lower()
    title = (job.get("title") or "").lower()
    location = (job.get("location") or "").lower()
    searchable = f"{title} {desc} {location}"
    sunday_flag = any(kw in searchable for kw in SUNDAY_KEYWORDS)
    accessible = "montgomery" in searchable
    return accessible, sunday_flag


def _annotate_credit(jobs: list[dict]) -> list[dict]:
    """Annotate jobs with credit_blocked flag based on credit_check field."""
    results = []
    for job in jobs:
        blocked = job.get("credit_check") == "required"
        results.append({**job, "credit_blocked": blocked})
    return results


async def match_jobs(
    profile: UserProfile, db_session: AsyncSession,
    benefits_profile: BenefitsProfile | None = None,
) -> list[ScoredJobMatch]:
    """Run the full filter→score→rank pipeline. Returns flat PVS-ranked list."""
    listings = await get_all_job_listings(db_session)
    if not listings:
        return []

    stops_with_routes = await _get_stops_with_routes(db_session)

    jobs = _filter_by_industry(listings, profile.target_industries)
    jobs = _filter_by_schedule(jobs, profile.schedule_type)
    jobs = _filter_by_transit(
        jobs, profile.transit_dependent, stops_with_routes,
        schedule_type=profile.schedule_type.value,
    )
    jobs = _annotate_credit(jobs)

    policies = await get_all_employer_policies(db_session)
    jobs = filter_jobs_by_record(jobs, profile.record_profile, policies)

    ctx = ScoringContext(
        user_zip=profile.zip_code,
        transit_dependent=profile.transit_dependent,
        schedule_type=profile.schedule_type,
        barriers=profile.primary_barriers,
        benefits_profile=benefits_profile,
        target_industries=profile.target_industries,
    )
    return rank_all_jobs(jobs, ctx)

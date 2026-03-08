"""Job matcher: filter pipeline for personalized job matching."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.queries_jobs import get_all_job_listings
from app.modules.matching.job_keywords import INDUSTRY_KEYWORDS, SCHEDULE_CONFLICT_KEYWORDS, SUNDAY_KEYWORDS
from app.modules.matching.job_scoring import rank_and_bucket, job_search_text
from app.modules.matching.types import AvailableHours, ScoredJobMatch, UserProfile


async def _get_transit_stops(db_session: AsyncSession) -> list[dict]:
    """Fetch all transit stops from DB."""
    result = await db_session.execute(text("SELECT * FROM transit_stops"))
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
    jobs: list[dict], transit_dependent: bool, transit_stops: list[dict],
) -> list[dict]:
    """Annotate jobs with transit_accessible and sunday_flag."""
    if not transit_dependent:
        return [{**j, "transit_accessible": True, "sunday_flag": False} for j in jobs]

    results = []
    for job in jobs:
        desc = (job.get("description") or "").lower()
        title = (job.get("title") or "").lower()
        location = (job.get("location") or "").lower()
        searchable = f"{title} {desc} {location}"

        sunday_flag = any(kw in searchable for kw in SUNDAY_KEYWORDS)

        accessible = _is_near_transit(job, transit_stops) if transit_stops else False

        results.append({**job, "transit_accessible": accessible, "sunday_flag": sunday_flag})
    return results


def _is_near_transit(job: dict, stops: list[dict], threshold_km: float = 3.0) -> bool:
    """Check if job location is within threshold of any transit stop.

    Falls back to text matching on location/stop_name if no coordinates.
    """
    job_location = (job.get("location") or "").lower()
    if not job_location:
        return False

    for stop in stops:
        stop_name = (stop.get("stop_name") or "").lower()
        if stop_name and stop_name in job_location:
            return True

    return False


def _annotate_credit(jobs: list[dict]) -> list[dict]:
    """Annotate jobs with credit_blocked flag based on credit_check field."""
    results = []
    for job in jobs:
        blocked = job.get("credit_check") == "required"
        results.append({**job, "credit_blocked": blocked})
    return results


async def match_jobs(
    profile: UserProfile, db_session: AsyncSession,
) -> tuple[list[ScoredJobMatch], list[ScoredJobMatch], list[ScoredJobMatch]]:
    """Run the full filter→score→rank pipeline. Returns (strong, possible, after_repair)."""
    listings = await get_all_job_listings(db_session)
    if not listings:
        return [], [], []

    transit_stops = await _get_transit_stops(db_session)

    jobs = _filter_by_industry(listings, profile.target_industries)
    jobs = _filter_by_schedule(jobs, profile.schedule_type)
    jobs = _filter_by_transit(jobs, profile.transit_dependent, transit_stops)
    jobs = _annotate_credit(jobs)

    return rank_and_bucket(jobs, profile.work_history, profile.transit_dependent)

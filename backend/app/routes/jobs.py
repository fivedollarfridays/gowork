"""GET /api/jobs — job listings with barrier, transit, and industry filters."""

import asyncio

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.queries import get_all_employers, get_all_transit_routes
from app.core.queries_jobs import get_job_listing_by_id

router = APIRouter(prefix="/api/jobs", tags=["jobs"])

CREDIT_CHECK_INDUSTRIES = {"banking", "finance", "insurance"}


def requires_credit_check(license_type: str | None) -> bool:
    """Return True if the employer's license type implies a credit check."""
    if not license_type:
        return False
    return license_type.lower() in CREDIT_CHECK_INDUSTRIES


def is_transit_accessible(route: dict, schedule_type: str) -> bool:
    """Check if a transit route supports the given schedule type.

    M-Transit: no Sunday service; weekday hours ~5am-9pm.
    """
    weekday_end = route.get("weekday_end", "")
    try:
        end_hour = int(weekday_end.split(":")[0])
    except (ValueError, IndexError):
        return True
    if schedule_type == "night" and end_hour < 22:
        return False
    return True


def _enrich_job(job: dict, employer_map: dict, transit_routes: list[dict]) -> dict:
    """Add industry, credit_check_required, transit_info, and application_steps."""
    employer = employer_map.get(job.get("company", ""))
    industry = employer["industry"] if employer else None
    license_type = employer.get("license_type") if employer else None

    credit_required = "yes" if requires_credit_check(license_type) else "no"

    transit_info = None
    if employer and transit_routes:
        transit_info = {
            "accessible": True,
            "routes": [{"route_number": r["route_number"], "route_name": r["route_name"]}
                       for r in transit_routes],
            "schedule": "Mon-Sat, no Sunday service",
        }

    return {
        **job,
        "industry": industry,
        "credit_check_required": credit_required,
        "fair_chance": bool(job.get("fair_chance")),
        "transit_info": transit_info,
        "application_steps": _application_steps(job, credit_required),
    }


def _application_steps(job: dict, credit_required: str) -> list[str]:
    """Generate application steps for a job listing."""
    steps = [f"Apply online at {job['url']}" if job.get("url") else "Contact employer directly"]
    if credit_required == "yes":
        steps.append("Note: credit check required — consider credit repair resources first")
    steps.append("Bring government-issued ID and Social Security card")
    if job.get("company"):
        steps.append(f"Follow up with {job['company']} within 5 business days")
    return steps


@router.get("/")
async def list_jobs(
    db: AsyncSession = Depends(get_db),
    barriers: str | None = Query(None, description="Comma-separated barriers (e.g. credit,transportation)"),
    transit_accessible: bool | None = Query(None),
    industry: str | None = Query(None),
    source: str | None = Query(None, description="Filter by source (brightdata, jsearch, honestjobs)"),
    fair_chance: bool | None = Query(None, description="Filter to fair-chance employers only"),
) -> dict:
    """List aggregated jobs with optional filters."""
    from app.integrations.job_aggregator import JobAggregator

    agg = JobAggregator(db)
    jobs, employers, transit_routes = await asyncio.gather(
        agg.search(source=source, fair_chance=bool(fair_chance)),
        get_all_employers(db),
        get_all_transit_routes(db),
    )

    employer_map = {e["name"]: e for e in employers}
    enriched = [_enrich_job(j, employer_map, transit_routes) for j in jobs]

    if industry:
        enriched = [j for j in enriched if j.get("industry") == industry]

    if transit_accessible:
        enriched = [
            j for j in enriched
            if j.get("transit_info") and j["transit_info"].get("accessible")
        ]

    if barriers:
        barrier_list = [b.strip() for b in barriers.split(",")]
        if "credit" in barrier_list:
            enriched = [j for j in enriched if j.get("credit_check_required") != "yes"]

    return {"jobs": enriched, "total": len(enriched)}


@router.get("/{job_id}")
async def get_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get a single job with details, transit info, and application steps."""
    job = await get_job_listing_by_id(db, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    employers, transit_routes = await asyncio.gather(
        get_all_employers(db),
        get_all_transit_routes(db),
    )
    employer_map = {e["name"]: e for e in employers}

    return _enrich_job(job, employer_map, transit_routes)

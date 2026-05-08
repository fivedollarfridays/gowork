"""GET /api/jobs — public listing fetch with verification-tier projection.

Each job dict carries ``verification: {tier, verified_at,
intake_complete: bool} | null`` projected from ``listing_verifications``
(T24.1 / T24.2). Integrity invariants (see ``docs/integrity-charter.md``):

* ``intake_json`` is NEVER on the public payload — only the boolean
  ``intake_complete`` derived from ``intake_completed_at IS NOT NULL``.
  The queries-layer helper already strips ``intake_json``; this route
  belt-and-suspenders that by projecting only three documented keys.
* The verification join is ONE batched call to
  ``get_public_verification_summary(listing_ids)`` — no N+1.
* ``Cache-Control: public, max-age=60`` mirrors T23.6; the surface
  stays accessible without forcing login (anonymous-first).
"""

import asyncio

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.queries import get_all_employers, get_all_transit_routes
from app.core.queries_jobs import get_job_listing_by_id
from app.core.queries_listings_verification import (
    get_public_verification_summary,
)
from app.core.rate_limit import RateLimiter, require_rate_limit

router = APIRouter(prefix="/api/jobs", tags=["jobs"])

_list_rate_limiter = RateLimiter(max_requests=60, window_seconds=60)
_check_list_rate = require_rate_limit(_list_rate_limiter)
_detail_rate_limiter = RateLimiter(max_requests=120, window_seconds=60)
_check_detail_rate = require_rate_limit(_detail_rate_limiter)

CREDIT_CHECK_INDUSTRIES = {"banking", "finance", "insurance"}
_CACHE_CONTROL = "public, max-age=60"


def _project_verification(row: dict | None) -> dict | None:
    """Project a queries-layer summary row to the public response shape.

    Returns ``None`` when no verification row exists. Otherwise returns
    exactly three documented keys — additions to the queries-layer
    dict (e.g. ``employer_account_id``) can't silently leak through.
    """
    if row is None:
        return None
    return {
        "tier": row["verification_tier"],
        "verified_at": row["verified_at"],
        "intake_complete": bool(row["intake_complete"]),
    }


def requires_credit_check(license_type: str | None) -> bool:
    """Return True if the employer's license type implies a credit check."""
    if not license_type:
        return False
    return license_type.lower() in CREDIT_CHECK_INDUSTRIES


def is_transit_accessible(route: dict, schedule_type: str) -> bool:
    """Check if a transit route supports the given schedule type.

    General transit check: weekday end hour determines night shift access.
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


def _apply_query_filters(
    jobs: list[dict], industry: str | None,
    transit_accessible: bool | None, barriers: str | None,
) -> list[dict]:
    """Apply industry / transit / barrier filters to enriched jobs."""
    if industry:
        jobs = [j for j in jobs if j.get("industry") == industry]
    if transit_accessible:
        jobs = [j for j in jobs if (j.get("transit_info") or {}).get("accessible")]
    if barriers and "credit" in [b.strip() for b in barriers.split(",")]:
        jobs = [j for j in jobs if j.get("credit_check_required") != "yes"]
    return jobs


async def _attach_verification(db: AsyncSession, jobs: list[dict]) -> None:
    """Add `verification` to each job via ONE batched read (no N+1)."""
    listing_ids = [int(j["id"]) for j in jobs if j.get("id") is not None]
    if not listing_ids:
        # Empty result page — annotate every job with verification=null
        # without paying for a no-op DB call.
        for job in jobs:
            job["verification"] = None
        return
    summary = await get_public_verification_summary(db, listing_ids)
    for job in jobs:
        row = summary.get(int(job["id"])) if job.get("id") is not None else None
        job["verification"] = _project_verification(row)


@router.get("/")
async def list_jobs(
    response: Response,
    db: AsyncSession = Depends(get_db),
    barriers: str | None = Query(None, description="Comma-separated barriers (e.g. credit,transportation)"),
    transit_accessible: bool | None = Query(None),
    industry: str | None = Query(None),
    source: str | None = Query(None, description="Filter by source (brightdata, honestjobs)"),
    fair_chance: bool | None = Query(None, description="Filter to fair-chance employers only"),
    _: None = Depends(_check_list_rate),
) -> dict:
    """List aggregated jobs with optional filters + verification tier.

    intake_json EXCLUDED from response (see module docstring). One
    batched verification read; ``Cache-Control: public, max-age=60``.
    """
    from app.integrations.job_aggregator import JobAggregator

    agg = JobAggregator(db)
    jobs, employers, transit_routes = await asyncio.gather(
        agg.search(source=source, fair_chance=bool(fair_chance)),
        get_all_employers(db),
        get_all_transit_routes(db),
    )

    employer_map = {e["name"]: e for e in employers}
    enriched = [_enrich_job(j, employer_map, transit_routes) for j in jobs]
    enriched = _apply_query_filters(enriched, industry, transit_accessible, barriers)
    await _attach_verification(db, enriched)

    response.headers["Cache-Control"] = _CACHE_CONTROL
    return {"jobs": enriched, "total": len(enriched)}


@router.get("/{job_id}")
async def get_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(_check_detail_rate),
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

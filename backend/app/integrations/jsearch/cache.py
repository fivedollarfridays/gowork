"""Cache JSearch results into job_listings table."""

import re
from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.queries_jobs import insert_job_listings
from app.integrations.jsearch.types import JSearchJobRecord

_FIELD_LIMITS = {
    "title": 500,
    "company": 200,
    "location": 200,
    "description": 5000,
    "url": 2000,
}

_TITLE_EXCLUDE = re.compile(
    r"\b(?:CEO|CFO|CTO|COO|VP|Vice\s+President|Director|Attorney|"
    r"Physician|Surgeon|Partner|Managing\s+Director|Chief)\b",
    re.IGNORECASE,
)

_SALARY_THRESHOLD = 80_000
_HOURS_PER_YEAR = 2080
_CACHE_TTL_HOURS = 24


def _should_exclude(job: dict) -> bool:
    """Return True if job should be excluded (executive title or high salary)."""
    title = job.get("job_title", "")
    if title and _TITLE_EXCLUDE.search(title):
        return True
    max_salary = job.get("job_max_salary")
    period = (job.get("job_salary_period") or "").upper()
    if max_salary is not None and max_salary > 0:
        annual = max_salary
        if period in ("HOUR", "HOURLY"):
            annual = max_salary * _HOURS_PER_YEAR
        if annual > _SALARY_THRESHOLD:
            return True
    return False


def _truncate(value: str | None, limit: int) -> str | None:
    if value is None:
        return None
    return value[:limit]


def build_location(city: str | None, state: str | None) -> str | None:
    if city and state:
        return f"{city}, {state}"
    return city or state or None


def parse_jsearch_jobs(raw_jobs: list[dict]) -> list[JSearchJobRecord]:
    """Parse raw JSearch JSON into typed records. Skips excluded entries."""
    results = []
    for job in raw_jobs:
        title = job.get("job_title")
        if not title:
            continue
        if _should_exclude(job):
            continue
        location = build_location(job.get("job_city"), job.get("job_state"))
        results.append(JSearchJobRecord(
            title=_truncate(title, _FIELD_LIMITS["title"]),
            company=_truncate(job.get("employer_name"), _FIELD_LIMITS["company"]),
            location=_truncate(location, _FIELD_LIMITS["location"]),
            description=_truncate(job.get("job_description"), _FIELD_LIMITS["description"]),
            url=_truncate(job.get("job_apply_link"), _FIELD_LIMITS["url"]),
            salary_min=job.get("job_min_salary"),
            salary_max=job.get("job_max_salary"),
            salary_type=normalize_period(job.get("job_salary_period")),
            employment_type=job.get("job_employment_type"),
        ))
    return results


def normalize_period(period: str | None) -> str | None:
    if not period:
        return None
    p = period.upper()
    if p in ("HOUR", "HOURLY"):
        return "hourly"
    if p in ("YEAR", "YEARLY", "ANNUAL"):
        return "annual"
    return period.lower()


async def _get_existing_urls(
    session: AsyncSession, urls: list[str],
) -> set[str]:
    """Fetch URLs that already exist in job_listings."""
    if not urls:
        return set()
    placeholders = ", ".join(f":u{i}" for i in range(len(urls)))
    params = {f"u{i}": url for i, url in enumerate(urls)}
    result = await session.execute(
        text(f"SELECT url FROM job_listings WHERE url IN ({placeholders})"),
        params,
    )
    return {row[0] for row in result}


async def store_jsearch_results(
    session: AsyncSession, request_id: str, raw_jobs: list[dict],
) -> int:
    """Parse, deduplicate by URL, and insert JSearch results. Returns count."""
    parsed = parse_jsearch_jobs(raw_jobs)
    if not parsed:
        return 0

    incoming_urls = [j.url for j in parsed if j.url]
    existing_urls = await _get_existing_urls(session, incoming_urls)

    now_dt = datetime.now(timezone.utc)
    now = now_dt.isoformat()
    expires = (now_dt + timedelta(hours=_CACHE_TTL_HOURS)).isoformat()
    source = f"jsearch:{request_id}"

    listings = []
    for job in parsed:
        if job.url and job.url in existing_urls:
            continue
        listings.append({
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "description": job.description,
            "url": job.url,
            "source": source,
            "scraped_at": now,
            "expires_at": expires,
        })

    return await insert_job_listings(session, listings)

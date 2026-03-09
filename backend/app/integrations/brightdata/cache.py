"""Cache BrightData crawl results into job_listings table."""

import re
from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.queries_jobs import insert_job_listings
from app.integrations.brightdata.types import BrightDataJobRecord
from app.modules.benefits.thresholds import HOURS_PER_YEAR as _HOURS_PER_YEAR


_FIELD_LIMITS = {"title": 500, "company": 200, "location": 200, "description": 5000, "url": 2000}

_TITLE_EXCLUDE = re.compile(
    r"\b(?:CEO|CFO|CTO|COO|VP|Vice\s+President|Director|Attorney|"
    r"Physician|Surgeon|Partner|Managing\s+Director|Chief)\b",
    re.IGNORECASE,
)
_SALARY_YEARLY = re.compile(r"\$[\d,]+(?:\.\d+)?/(?:yr|year)", re.IGNORECASE)
_SALARY_HOURLY = re.compile(r"\$([\d,]+(?:\.\d+)?)/hr", re.IGNORECASE)
_SALARY_THRESHOLD = 80_000


def _parse_salary_yearly(salary: str) -> float | None:
    """Extract annual salary from string. Returns None if unparseable."""
    m = _SALARY_YEARLY.search(salary)
    if m:
        num_str = m.group(0).lstrip("$").split("/")[0].replace(",", "")
        return float(num_str)
    m = _SALARY_HOURLY.search(salary)
    if m:
        return float(m.group(1).replace(",", "")) * _HOURS_PER_YEAR
    return None


def _should_exclude(job: dict) -> bool:
    """Return True if job should be excluded (executive title or high salary)."""
    title = job.get("title")
    if not title:
        return False
    if _TITLE_EXCLUDE.search(title):
        return True
    salary = job.get("salary", "")
    if salary:
        annual = _parse_salary_yearly(salary)
        if annual is not None and annual > _SALARY_THRESHOLD:
            return True
    return False


def _truncate(value: str | None, limit: int) -> str | None:
    """Truncate a string to limit length, or return None."""
    if value is None:
        return None
    return value[:limit]


def _get_field(job: dict, *keys: str) -> str | None:
    """Return the first non-empty value found among the given keys."""
    for k in keys:
        v = job.get(k)
        if v:
            return v
    return None


def parse_brightdata_jobs(raw_jobs: list[dict]) -> list[BrightDataJobRecord]:
    """Parse raw BrightData JSON into typed records. Skips entries without title or excluded."""
    results = []
    for job in raw_jobs:
        title = _get_field(job, "title", "job_title", "name")
        if not title:
            continue
        # Normalize for exclusion check
        normalized = {**job, "title": title}
        if _should_exclude(normalized):
            continue
        results.append(BrightDataJobRecord(
            title=_truncate(title, _FIELD_LIMITS["title"]),
            company=_truncate(_get_field(job, "company", "company_name"), _FIELD_LIMITS["company"]),
            location=_truncate(_get_field(job, "location"), _FIELD_LIMITS["location"]),
            description=_truncate(_get_field(job, "description", "description_text"), _FIELD_LIMITS["description"]),
            url=_truncate(_get_field(job, "url", "apply_link"), _FIELD_LIMITS["url"]),
        ))
    return results


async def _get_existing_urls(
    session: AsyncSession, urls: list[str],
) -> set[str]:
    """Fetch URLs that already exist in job_listings for deduplication."""
    if not urls:
        return set()
    placeholders = ", ".join(f":u{i}" for i in range(len(urls)))
    params = {f"u{i}": url for i, url in enumerate(urls)}
    result = await session.execute(
        text(f"SELECT url FROM job_listings WHERE url IN ({placeholders})"),
        params,
    )
    return {row[0] for row in result}


async def store_crawl_results(
    session: AsyncSession, snapshot_id: str, raw_jobs: list[dict],
) -> int:
    """Parse, deduplicate by URL, and insert crawl results. Returns insert count."""
    parsed = parse_brightdata_jobs(raw_jobs)
    if not parsed:
        return 0

    incoming_urls = [j.url for j in parsed if j.url]
    existing_urls = await _get_existing_urls(session, incoming_urls)

    now_dt = datetime.now(timezone.utc)
    now = now_dt.isoformat()
    expires = (now_dt + timedelta(days=30)).isoformat()
    source = f"brightdata:{snapshot_id}"

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

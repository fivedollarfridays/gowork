"""Cache BrightData crawl results into job_listings table."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.queries_jobs import insert_job_listings
from app.integrations.brightdata.types import BrightDataJobRecord


_FIELD_LIMITS = {"title": 500, "company": 200, "location": 200, "description": 5000, "url": 2000}


def _truncate(value: str | None, limit: int) -> str | None:
    """Truncate a string to limit length, or return None."""
    if value is None:
        return None
    return value[:limit]


def parse_brightdata_jobs(raw_jobs: list[dict]) -> list[BrightDataJobRecord]:
    """Parse raw BrightData JSON into typed records. Skips entries without title."""
    results = []
    for job in raw_jobs:
        if not job.get("title"):
            continue
        results.append(BrightDataJobRecord(
            title=_truncate(job["title"], _FIELD_LIMITS["title"]),
            company=_truncate(job.get("company"), _FIELD_LIMITS["company"]),
            location=_truncate(job.get("location"), _FIELD_LIMITS["location"]),
            description=_truncate(job.get("description"), _FIELD_LIMITS["description"]),
            url=_truncate(job.get("url"), _FIELD_LIMITS["url"]),
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

"""Cache BrightData crawl results into job_listings table."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.queries import insert_job_listings
from app.integrations.brightdata.types import BrightDataJobRecord


def parse_brightdata_jobs(raw_jobs: list[dict]) -> list[BrightDataJobRecord]:
    """Parse raw BrightData JSON into typed records. Skips entries without title."""
    results = []
    for job in raw_jobs:
        if not job.get("title"):
            continue
        results.append(BrightDataJobRecord(
            title=job["title"],
            company=job.get("company"),
            location=job.get("location"),
            description=job.get("description"),
            url=job.get("url"),
        ))
    return results


async def store_crawl_results(
    session: AsyncSession, snapshot_id: str, raw_jobs: list[dict],
) -> int:
    """Parse, deduplicate by URL, and insert crawl results. Returns insert count."""
    parsed = parse_brightdata_jobs(raw_jobs)
    if not parsed:
        return 0

    # Fetch existing URLs for deduplication — only check URLs in this batch
    incoming_urls = [j.url for j in parsed if j.url]
    existing_urls: set[str] = set()
    if incoming_urls:
        # Use batched IN query instead of full table scan
        placeholders = ", ".join(f":u{i}" for i in range(len(incoming_urls)))
        params = {f"u{i}": url for i, url in enumerate(incoming_urls)}
        result = await session.execute(
            text(f"SELECT url FROM job_listings WHERE url IN ({placeholders})"),
            params,
        )
        existing_urls = {row[0] for row in result}

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

"""Pre-crawl Montgomery job listings via BrightData."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.integrations.brightdata.cache import store_crawl_results
from app.integrations.brightdata.client import BrightDataClient
from app.integrations.brightdata.polling import poll_until_ready


def build_search_urls() -> list[str]:
    """Return Indeed and LinkedIn search URLs for Montgomery, AL."""
    return [
        "https://www.indeed.com/jobs?q=&l=Montgomery%2C+AL&radius=25",
        "https://www.indeed.com/jobs?q=warehouse&l=Montgomery%2C+AL",
        "https://www.indeed.com/jobs?q=healthcare&l=Montgomery%2C+AL",
        "https://www.indeed.com/jobs?q=customer+service&l=Montgomery%2C+AL",
        "https://www.linkedin.com/jobs/search/?location=Montgomery%2C+Alabama",
    ]


async def _has_recent_data(session: AsyncSession) -> bool:
    """Check if brightdata job listings less than 24h old exist."""
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    result = await session.execute(
        text("SELECT COUNT(*) FROM job_listings WHERE source LIKE 'brightdata:%' AND scraped_at > :cutoff"),
        {"cutoff": cutoff},
    )
    return result.scalar() > 0


async def precrawl_montgomery_jobs(db_session: AsyncSession) -> dict:
    """Trigger crawl of Montgomery job sites, poll, and cache results."""
    if await _has_recent_data(db_session):
        return {"snapshot_id": None, "jobs_cached": 0, "skipped": True}

    settings = get_settings()
    async with BrightDataClient(settings.brightdata_api_key, settings.brightdata_dataset_id) as client:
        urls = build_search_urls()
        snapshot_id = await client.trigger_crawl(urls)
        result = await poll_until_ready(client, snapshot_id)
        count = await store_crawl_results(db_session, snapshot_id, result.jobs)

    return {"snapshot_id": snapshot_id, "jobs_cached": count, "skipped": False}

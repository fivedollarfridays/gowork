"""Pre-crawl Montgomery job listings via BrightData."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.integrations.brightdata.cache import store_crawl_results
from app.integrations.brightdata.client import BrightDataClient
from app.integrations.brightdata.polling import poll_until_ready


_KEYWORDS = [
    "jobs", "warehouse", "healthcare", "customer service", "retail",
    "manufacturing", "food service", "construction", "driver",
    "cashier", "cleaning", "security", "maintenance",
    "administrative", "entry level",
]

_LOCATION = "Montgomery, AL"


def build_search_urls() -> list[str]:
    """Return Indeed search URLs for Montgomery, AL jobs."""
    from urllib.parse import quote_plus
    urls: list[str] = []
    for kw in _KEYWORDS:
        q = quote_plus(kw) if kw else ""
        loc = quote_plus(_LOCATION)
        url = f"https://www.indeed.com/jobs?q={q}&l={loc}&fromage=7"
        urls.append(url)
    return urls


def build_keyword_searches() -> list[dict]:
    """Return structured keyword searches for Montgomery, AL jobs (Indeed + LinkedIn)."""
    searches: list[dict] = []
    for domain in ("indeed.com",):
        for kw in _KEYWORDS:
            searches.append({
                "country": "US",
                "domain": domain,
                "keyword_search": kw,
                "location": _LOCATION,
            })
    return searches


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
        searches = build_keyword_searches()
        snapshot_id = await client.trigger_keyword_crawl(searches)
        result = await poll_until_ready(client, snapshot_id)
        count = await store_crawl_results(db_session, snapshot_id, result.jobs)

    return {"snapshot_id": snapshot_id, "jobs_cached": count, "skipped": False}

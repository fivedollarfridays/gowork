"""Pre-crawl Montgomery job listings via BrightData."""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.integrations.brightdata.cache import store_crawl_results
from app.integrations.brightdata.client import BrightDataClient
from app.integrations.brightdata.polling import poll_until_ready

logger = logging.getLogger(__name__)

_KEYWORDS = [
    "jobs", "warehouse", "healthcare", "customer service", "retail",
    "manufacturing", "food service", "construction", "driver",
    "cashier", "cleaning", "security", "maintenance",
    "administrative", "entry level",
]

_LOCATION = "Montgomery, AL"
_DEFAULT_DOMAINS = ["indeed.com"]


def get_crawl_domains() -> list[str]:
    """Parse configured job board domains, falling back to indeed.com."""
    settings = get_settings()
    raw = settings.brightdata_job_domains
    if not raw or not raw.strip():
        return list(_DEFAULT_DOMAINS)
    domains = [d.strip() for d in raw.split(",") if d.strip()]
    return domains if domains else list(_DEFAULT_DOMAINS)


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
    """Return structured keyword searches for Montgomery, AL jobs across configured domains."""
    domains = get_crawl_domains()
    searches: list[dict] = []
    for domain in domains:
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


def _searches_for_domain(domain: str) -> list[dict]:
    """Build keyword searches for a single domain."""
    return [
        {"country": "US", "domain": domain, "keyword_search": kw, "location": _LOCATION}
        for kw in _KEYWORDS
    ]


async def _crawl_domain(
    client: BrightDataClient, db_session: AsyncSession, domain: str,
) -> int:
    """Crawl a single domain: trigger, poll, store. Returns cached count."""
    searches = _searches_for_domain(domain)
    snapshot_id = await client.trigger_keyword_crawl(searches)
    result = await poll_until_ready(client, snapshot_id)
    return await store_crawl_results(db_session, snapshot_id, result.jobs)


async def precrawl_montgomery_jobs(db_session: AsyncSession) -> dict:
    """Trigger crawl of Montgomery job sites, poll, and cache results.

    Crawls each configured domain independently with partial failure
    tolerance: if one domain fails, others still proceed.
    """
    if await _has_recent_data(db_session):
        return {"snapshot_id": None, "jobs_cached": 0, "skipped": True, "errors": []}

    settings = get_settings()
    domains = get_crawl_domains()
    total_cached = 0
    errors: list[str] = []
    snapshot_id: str | None = None

    async with BrightDataClient(settings.brightdata_api_key, settings.brightdata_dataset_id) as client:
        for domain in domains:
            try:
                count = await _crawl_domain(client, db_session, domain)
                total_cached += count
                if snapshot_id is None:
                    snapshot_id = f"multi-{domain}"
            except Exception as exc:
                msg = f"{domain}: {exc}"
                logger.warning("Precrawl failed for %s: %s", domain, exc)
                errors.append(msg)

    return {
        "snapshot_id": snapshot_id,
        "jobs_cached": total_cached,
        "skipped": False,
        "errors": errors,
    }

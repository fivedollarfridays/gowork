"""TWC (Texas Workforce Commission) job adapter.

Fetches job listings from the TWC WorkInTexas.com job board API.
Degrades gracefully to empty list if API is unavailable.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import httpx

from app.integrations._http_retry import async_get_with_retry

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

_logger = logging.getLogger(__name__)

_TWC_SEARCH_URL = "https://www.workintexas.com/vosnet/api/jobs/search"
_TIMEOUT = 15.0
_MAX_RESULTS = 25


async def _fetch_twc_jobs(query: str, location: str) -> list[dict]:
    """Fetch jobs from TWC API. Returns raw job dicts."""
    params = {
        "keywords": query,
        "location": location,
        "radius": "25",
        "pageSize": str(_MAX_RESULTS),
        "page": "1",
    }
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        # Idempotent GET: retry on 5xx + connect errors (T13.92).
        resp = await async_get_with_retry(client, _TWC_SEARCH_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

    jobs = data if isinstance(data, list) else data.get("jobs", data.get("results", []))
    return [_normalize(j) for j in jobs[:_MAX_RESULTS]]


def _normalize(raw: dict) -> dict:
    """Normalize a TWC job listing to the standard format."""
    return {
        "title": raw.get("title", raw.get("jobTitle", "Unknown")),
        "company": raw.get("company", raw.get("employer", "")),
        "location": raw.get("location", raw.get("city", "")),
        "url": raw.get("url", raw.get("jobUrl", "")),
        "source": "twc",
        "fair_chance": 0,
    }


class TWCJobAdapter:
    """Adapter for TWC WorkInTexas.com job listings."""

    async def fetch_jobs(
        self, session: AsyncSession, query: str, location: str,
    ) -> list[dict]:
        """Fetch jobs from TWC. Returns empty list on failure."""
        try:
            return await _fetch_twc_jobs(query, location)
        except Exception:
            _logger.warning("TWC API fetch failed", exc_info=True)
            return []

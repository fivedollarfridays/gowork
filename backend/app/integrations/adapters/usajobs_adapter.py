"""USAJobs federal job adapter.

Fetches job listings from https://data.usajobs.gov/api/search.
Requires USAJOBS_API_KEY and USAJOBS_EMAIL env vars.
Degrades gracefully to empty list if API key is missing or API is down.
"""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

_logger = logging.getLogger(__name__)

_USAJOBS_URL = "https://data.usajobs.gov/api/search"
_TIMEOUT = 15.0
_MAX_RESULTS = 25


def _get_api_key() -> str:
    """Get USAJobs API key from environment."""
    return os.environ.get("USAJOBS_API_KEY", "")


def _get_email() -> str:
    """Get USAJobs contact email from environment."""
    return os.environ.get("USAJOBS_EMAIL", "")


async def _fetch_usajobs(query: str, location: str) -> list[dict]:
    """Fetch jobs from USAJobs API. Returns normalized job dicts."""
    api_key = _get_api_key()
    email = _get_email()
    if not api_key:
        _logger.warning("USAJOBS_API_KEY not set; skipping USAJobs fetch")
        return []

    headers = {
        "Authorization-Key": api_key,
        "User-Agent": email or "montgowork@example.com",
        "Host": "data.usajobs.gov",
    }
    params = {
        "Keyword": query,
        "LocationName": location,
        "ResultsPerPage": str(_MAX_RESULTS),
    }

    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.get(_USAJOBS_URL, params=params, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    results = (
        data.get("SearchResult", {})
        .get("SearchResultItems", [])
    )
    return [_normalize(item) for item in results[:_MAX_RESULTS]]


def _normalize(item: dict) -> dict:
    """Normalize a USAJobs result item to the standard format."""
    match_data = item.get("MatchedObjectDescriptor", item)
    positions = match_data.get("PositionLocation", [{}])
    location = positions[0].get("LocationName", "") if positions else ""

    return {
        "title": match_data.get("PositionTitle", "Unknown"),
        "company": match_data.get("OrganizationName", "U.S. Government"),
        "location": location,
        "url": match_data.get("PositionURI", match_data.get("ApplyURI", [""])[0] if isinstance(match_data.get("ApplyURI"), list) else ""),
        "source": "usajobs",
        "fair_chance": 0,
    }


class USAJobsJobAdapter:
    """Adapter for USAJobs federal job listings."""

    async def fetch_jobs(
        self, session: AsyncSession, query: str, location: str,
    ) -> list[dict]:
        """Fetch jobs from USAJobs. Returns empty list on failure."""
        if not _get_api_key():
            return []
        try:
            return await _fetch_usajobs(query, location)
        except Exception:
            _logger.warning("USAJobs API fetch failed", exc_info=True)
            return []

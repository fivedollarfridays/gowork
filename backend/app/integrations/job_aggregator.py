"""Unified job aggregator — parallel fetch from all sources with dedup."""

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.dedup import deduplicate_listings
from app.integrations.jsearch.cache import store_jsearch_results
from app.integrations.jsearch.types import JSearchJobRecord

logger = logging.getLogger(__name__)


class JobAggregator:
    """Aggregates jobs from BrightData, JSearch, and Honest Jobs."""

    def __init__(self, session: AsyncSession, jsearch_client=None):
        self._session = session
        self._jsearch = jsearch_client

    async def search(
        self,
        query: str = "jobs",
        location: str = "Montgomery, AL",
        source: str | None = None,
        fair_chance: bool = False,
    ) -> list[dict]:
        """Fetch from all sources, deduplicate, and return unified list."""
        tasks = [
            self._brightdata_cached(),
            self._honestjobs_cached(),
        ]
        if self._jsearch:
            tasks.append(self._jsearch_fetch(query, location))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        all_jobs = []
        for result in results:
            if isinstance(result, Exception):
                logger.warning("Source fetch failed: %s", result)
                continue
            all_jobs.extend(result)

        deduped = deduplicate_listings(all_jobs)

        if source:
            deduped = [j for j in deduped if _matches_source(j, source)]
        if fair_chance:
            deduped = [j for j in deduped if j.get("fair_chance") == 1]

        return deduped

    async def _brightdata_cached(self) -> list[dict]:
        """Fetch non-expired BrightData jobs from cache."""
        now = datetime.now(timezone.utc).isoformat()
        result = await self._session.execute(
            text(
                "SELECT * FROM job_listings "
                "WHERE source LIKE 'brightdata:%' "
                "AND (expires_at IS NULL OR expires_at > :now)"
            ),
            {"now": now},
        )
        return [dict(row._mapping) for row in result]

    async def _honestjobs_cached(self) -> list[dict]:
        """Fetch all Honest Jobs listings from cache."""
        result = await self._session.execute(
            text("SELECT * FROM job_listings WHERE source = 'honestjobs'")
        )
        return [dict(row._mapping) for row in result]

    async def _jsearch_fetch(self, query: str, location: str) -> list[dict]:
        """Fetch from JSearch API and cache results."""
        response = await self._jsearch.search_jobs(query, location)
        if not response.data:
            return []
        # Cache the results
        raw = [_record_to_raw(r) for r in response.data]
        await store_jsearch_results(self._session, response.request_id, raw)
        # Return as dicts
        return [_record_to_dict(r, response.request_id) for r in response.data]


def _record_to_raw(record: JSearchJobRecord) -> dict:
    """Convert JSearchJobRecord back to raw dict for caching."""
    return {
        "job_title": record.title,
        "employer_name": record.company,
        "job_city": record.location.split(",")[0].strip() if record.location and "," in record.location else record.location,
        "job_state": record.location.split(",")[1].strip() if record.location and "," in record.location else None,
        "job_description": record.description,
        "job_apply_link": record.url,
        "job_min_salary": record.salary_min,
        "job_max_salary": record.salary_max,
        "job_salary_period": record.salary_type,
        "job_employment_type": record.employment_type,
    }


def _record_to_dict(record: JSearchJobRecord, request_id: str) -> dict:
    """Convert JSearchJobRecord to job_listings dict."""
    return {
        "title": record.title,
        "company": record.company,
        "location": record.location,
        "description": record.description,
        "url": record.url,
        "source": f"jsearch:{request_id}",
        "fair_chance": 0,
    }


def _matches_source(job: dict, source_filter: str) -> bool:
    """Check if a job matches the source filter."""
    job_source = job.get("source", "")
    if source_filter == "brightdata":
        return job_source.startswith("brightdata:")
    if source_filter == "jsearch":
        return job_source.startswith("jsearch:")
    return job_source == source_filter

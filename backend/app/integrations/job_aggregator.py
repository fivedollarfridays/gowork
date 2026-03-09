"""Unified job aggregator — parallel fetch from all sources with dedup."""

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.dedup import deduplicate_listings

logger = logging.getLogger(__name__)


class JobAggregator:
    """Aggregates jobs from BrightData and Honest Jobs."""

    def __init__(self, session: AsyncSession):
        self._session = session

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


def _matches_source(job: dict, source_filter: str) -> bool:
    """Check if a job matches the source filter."""
    job_source = job.get("source", "")
    if source_filter == "brightdata":
        return job_source.startswith("brightdata:")
    return job_source == source_filter

"""Unified job aggregator — parallel fetch from city-configured adapters with dedup."""

import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.cities.config import get_city_config
from app.integrations.adapters.base import get_adapter
from app.integrations.dedup import deduplicate_listings

logger = logging.getLogger(__name__)


class JobAggregator:
    """Aggregates jobs from adapters configured in the active city's YAML."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def search(
        self,
        query: str = "jobs",
        location: str | None = None,
        source: str | None = None,
        fair_chance: bool = False,
    ) -> list[dict]:
        """Fetch from all city-configured adapters, deduplicate, and return unified list."""
        city_config = get_city_config()
        loc = location or city_config.location

        tasks = []
        for adapter_name in city_config.job_adapters:
            adapter = get_adapter(adapter_name)
            tasks.append(adapter.fetch_jobs(self._session, query, loc))

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


def _matches_source(job: dict, source_filter: str) -> bool:
    """Check if a job matches the source filter."""
    job_source = job.get("source", "")
    if source_filter == "brightdata":
        return job_source.startswith("brightdata:")
    return job_source == source_filter

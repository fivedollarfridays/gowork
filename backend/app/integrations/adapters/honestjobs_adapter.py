"""HonestJobs job adapter — wraps cached query logic from JobAggregator."""

from __future__ import annotations

from sqlalchemy import text


class HonestJobsJobAdapter:
    async def fetch_jobs(
        self, session, query: str, location: str
    ) -> list[dict]:
        result = await session.execute(
            text("SELECT * FROM job_listings WHERE source = 'honestjobs'")
        )
        return [dict(row._mapping) for row in result]

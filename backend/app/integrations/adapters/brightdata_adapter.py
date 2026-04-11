"""BrightData job adapter — wraps cached query logic from JobAggregator."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import text


class BrightDataJobAdapter:
    async def fetch_jobs(
        self, session, query: str, location: str
    ) -> list[dict]:
        now = datetime.now(timezone.utc).isoformat()
        result = await session.execute(
            text(
                "SELECT * FROM job_listings "
                "WHERE source LIKE 'brightdata:%' "
                "AND (expires_at IS NULL OR expires_at > :now)"
            ),
            {"now": now},
        )
        return [dict(row._mapping) for row in result]

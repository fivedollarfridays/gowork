"""Honest Jobs client — queries fair-chance listings from DB."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class HonestJobsClient:
    """Client for querying Honest Jobs fair-chance listings from the DB."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_listings(self) -> list[dict]:
        """Return all Honest Jobs listings."""
        result = await self._session.execute(
            text("SELECT * FROM job_listings WHERE source = 'honestjobs'")
        )
        return [dict(row._mapping) for row in result]

    async def get_fair_chance_listings(self) -> list[dict]:
        """Return all listings with fair_chance = 1 (any source)."""
        result = await self._session.execute(
            text("SELECT * FROM job_listings WHERE fair_chance = 1")
        )
        return [dict(row._mapping) for row in result]

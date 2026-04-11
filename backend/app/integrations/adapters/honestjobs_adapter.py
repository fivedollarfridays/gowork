"""HonestJobs job adapter — delegates to HonestJobsClient for cached listings."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.integrations.honestjobs.client import HonestJobsClient

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class HonestJobsJobAdapter:
    async def fetch_jobs(
        self, session: AsyncSession, query: str, location: str
    ) -> list[dict]:
        return await HonestJobsClient(session).get_listings()

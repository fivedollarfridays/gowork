"""BrightData job adapter stub — implementation in T1.4."""

from __future__ import annotations


class BrightDataJobAdapter:
    async def fetch_jobs(
        self, session, query: str, location: str
    ) -> list[dict]:
        raise NotImplementedError("BrightData adapter not yet implemented (T1.4)")

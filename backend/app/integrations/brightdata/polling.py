"""Exponential backoff poller for BrightData snapshot status."""

import asyncio
import random

from app.integrations.brightdata.client import BrightDataClient
from app.integrations.brightdata.types import (
    BrightDataAPIError,
    BrightDataTimeoutError,
    CrawlProgress,
    CrawlResult,
    CrawlStatus,
)


async def poll_until_ready(
    client: BrightDataClient,
    snapshot_id: str,
    max_retries: int = 30,
    base_delay: float = 2.0,
    max_delay: float = 60.0,
) -> CrawlResult:
    """Poll snapshot status with exponential backoff + jitter.

    Returns CrawlResult when the snapshot is ready.
    Raises BrightDataTimeoutError after max_retries.
    Raises BrightDataAPIError if the crawl fails.
    """
    for attempt in range(max_retries):
        result = await client.get_snapshot_status(snapshot_id)
        if isinstance(result, CrawlResult):
            return result
        if isinstance(result, CrawlProgress) and result.status == CrawlStatus.FAILED:
            raise BrightDataAPIError(0, f"Crawl {snapshot_id} failed")
        delay = min(base_delay * (2 ** attempt), max_delay) + random.uniform(0, 1)
        await asyncio.sleep(delay)
    raise BrightDataTimeoutError(
        f"Snapshot {snapshot_id} not ready after {max_retries} retries"
    )

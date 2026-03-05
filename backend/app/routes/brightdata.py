"""BrightData crawl routes — trigger, status, and pre-crawl."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.integrations.brightdata.client import BrightDataClient
from app.integrations.brightdata.cache import store_crawl_results
from app.integrations.brightdata.precrawl import precrawl_montgomery_jobs
from app.integrations.brightdata.types import (
    BrightDataAPIError,
    CrawlProgress,
    CrawlResult,
    CrawlStatus,
    CrawlStatusResponse,
    TriggerCrawlRequest,
    TriggerCrawlResponse,
)

router = APIRouter(prefix="/api/brightdata", tags=["brightdata"])


def _require_config():
    """Raise 503 if BrightData is not configured."""
    settings = get_settings()
    if not settings.brightdata_api_key or not settings.brightdata_dataset_id:
        raise HTTPException(503, "BrightData integration not configured")
    return settings


@router.post("/crawl")
async def trigger_crawl(
    request: TriggerCrawlRequest,
) -> TriggerCrawlResponse:
    """Trigger a BrightData crawl job. Returns snapshot_id immediately."""
    settings = _require_config()
    async with BrightDataClient(settings.brightdata_api_key, settings.brightdata_dataset_id) as client:
        try:
            snapshot_id = await client.trigger_crawl(request.urls)
        except BrightDataAPIError as e:
            raise HTTPException(502, e.detail)
    return TriggerCrawlResponse(
        snapshot_id=snapshot_id,
        status=CrawlStatus.STARTING,
        message="Crawl triggered",
    )


@router.get("/status/{snapshot_id}")
async def get_crawl_status(
    snapshot_id: str,
    db: AsyncSession = Depends(get_db),
) -> CrawlStatusResponse:
    """Check crawl status. Auto-caches results when done."""
    settings = _require_config()
    async with BrightDataClient(settings.brightdata_api_key, settings.brightdata_dataset_id) as client:
        try:
            result = await client.get_snapshot_status(snapshot_id)
        except BrightDataAPIError as e:
            raise HTTPException(502, e.detail)

    if isinstance(result, CrawlResult):
        count = await store_crawl_results(db, snapshot_id, result.jobs)
        return CrawlStatusResponse(
            snapshot_id=snapshot_id,
            status=CrawlStatus.READY,
            jobs_found=count,
            message=f"Crawl complete — {count} jobs cached",
        )
    return CrawlStatusResponse(
        snapshot_id=snapshot_id,
        status=result.status,
        progress_pct=result.progress_pct,
        message="Crawl in progress",
    )


@router.post("/precrawl")
async def run_precrawl(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Admin endpoint to pre-populate Montgomery job listings."""
    _require_config()
    return await precrawl_montgomery_jobs(db)

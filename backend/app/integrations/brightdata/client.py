"""Async HTTP client for BrightData Datasets API v3."""

import httpx

from app.integrations.brightdata.types import (
    BrightDataAPIError,
    BrightDataConfigError,
    CrawlProgress,
    CrawlResult,
    CrawlStatus,
)

BASE_URL = "https://api.brightdata.com/datasets/v3"


class BrightDataClient:
    """Typed wrapper around the BrightData Datasets API."""

    def __init__(self, api_key: str, dataset_id: str):
        if not api_key:
            raise BrightDataConfigError("BRIGHTDATA_API_KEY is not set")
        if not dataset_id:
            raise BrightDataConfigError("BRIGHTDATA_DATASET_ID is not set")
        self._api_key = api_key
        self._dataset_id = dataset_id
        self._http = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30.0,
        )

    def _raise_api_error(self, resp: httpx.Response) -> None:
        """Extract error detail from response and raise BrightDataAPIError."""
        detail = resp.text
        try:
            detail = resp.json().get("error", detail)
        except Exception:
            pass
        raise BrightDataAPIError(resp.status_code, detail)

    async def trigger_crawl(self, urls: list[str]) -> str:
        """Trigger an async crawl job. Returns the snapshot_id."""
        resp = await self._http.post(
            f"{BASE_URL}/trigger",
            params={"dataset_id": self._dataset_id, "format": "json"},
            json=[{"url": u} for u in urls],
        )
        if resp.status_code != 200:
            self._raise_api_error(resp)
        return resp.json()["snapshot_id"]

    async def get_snapshot_status(self, snapshot_id: str) -> CrawlProgress | CrawlResult:
        """Check snapshot status. Returns CrawlProgress (202) or CrawlResult (200)."""
        resp = await self._http.get(
            f"{BASE_URL}/snapshot/{snapshot_id}",
            params={"format": "json"},
        )
        if resp.status_code == 202:
            body = resp.json()
            return CrawlProgress(
                snapshot_id=snapshot_id,
                status=CrawlStatus.RUNNING,
                progress_pct=body.get("progress"),
            )
        if resp.status_code == 200:
            return CrawlResult(snapshot_id=snapshot_id, jobs=resp.json())
        self._raise_api_error(resp)

    async def close(self):
        """Close the underlying HTTP client."""
        await self._http.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        await self.close()

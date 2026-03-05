"""Tests for BrightData route endpoints."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.integrations.brightdata.types import (
    BrightDataAPIError,
    CrawlProgress,
    CrawlResult,
    CrawlStatus,
)

_CLIENT_PATCH = "app.routes.brightdata.BrightDataClient"
_SETTINGS_PATCH = "app.routes.brightdata.get_settings"
_STORE_PATCH = "app.routes.brightdata.store_crawl_results"
_PRECRAWL_PATCH = "app.routes.brightdata.precrawl_montgomery_jobs"


def _mock_settings(api_key: str = "key-123", dataset_id: str = "ds-123"):
    s = AsyncMock()
    s.brightdata_api_key = api_key
    s.brightdata_dataset_id = dataset_id
    return s


def _mock_client(**method_overrides):
    """Create a mock BrightDataClient that supports async context manager."""
    client = AsyncMock()
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)
    for name, value in method_overrides.items():
        setattr(client, name, value)
    return client


class TestTriggerCrawl:
    @pytest.mark.asyncio
    async def test_trigger_success(self):
        from app.main import app

        mock_client = _mock_client(
            trigger_crawl=AsyncMock(return_value="snap-abc"),
        )

        with (
            patch(_SETTINGS_PATCH, return_value=_mock_settings()),
            patch(_CLIENT_PATCH, return_value=mock_client),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as c:
                resp = await c.post("/api/brightdata/crawl", json={
                    "urls": ["https://indeed.com/jobs?l=Montgomery+AL"],
                })
        assert resp.status_code == 200
        data = resp.json()
        assert data["snapshot_id"] == "snap-abc"
        assert data["status"] == "starting"

    @pytest.mark.asyncio
    async def test_trigger_no_api_key(self):
        from app.main import app

        with patch(_SETTINGS_PATCH, return_value=_mock_settings(api_key="")):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as c:
                resp = await c.post("/api/brightdata/crawl", json={
                    "urls": ["https://indeed.com/jobs"],
                })
        assert resp.status_code == 503

    @pytest.mark.asyncio
    async def test_trigger_empty_urls_rejected(self):
        from app.main import app

        with patch(_SETTINGS_PATCH, return_value=_mock_settings()):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as c:
                resp = await c.post("/api/brightdata/crawl", json={"urls": []})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_trigger_api_error(self):
        from app.main import app

        mock_client = _mock_client(
            trigger_crawl=AsyncMock(side_effect=BrightDataAPIError(429, "rate limited")),
        )

        with (
            patch(_SETTINGS_PATCH, return_value=_mock_settings()),
            patch(_CLIENT_PATCH, return_value=mock_client),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as c:
                resp = await c.post("/api/brightdata/crawl", json={
                    "urls": ["https://indeed.com/jobs"],
                })
        assert resp.status_code == 502


class TestCrawlStatus:
    @pytest.mark.asyncio
    async def test_status_running(self):
        from app.main import app

        mock_client = _mock_client(
            get_snapshot_status=AsyncMock(return_value=CrawlProgress(
                snapshot_id="snap-abc", status=CrawlStatus.RUNNING, progress_pct=0.5,
            )),
        )

        with (
            patch(_SETTINGS_PATCH, return_value=_mock_settings()),
            patch(_CLIENT_PATCH, return_value=mock_client),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as c:
                resp = await c.get("/api/brightdata/status/snap-abc")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "running"
        assert data["progress_pct"] == 0.5

    @pytest.mark.asyncio
    async def test_status_ready_caches_results(self):
        from app.main import app

        jobs = [{"title": "Warehouse Worker"}, {"title": "CNA"}]
        mock_client = _mock_client(
            get_snapshot_status=AsyncMock(return_value=CrawlResult(snapshot_id="snap-abc", jobs=jobs)),
        )

        with (
            patch(_SETTINGS_PATCH, return_value=_mock_settings()),
            patch(_CLIENT_PATCH, return_value=mock_client),
            patch(_STORE_PATCH, new_callable=AsyncMock, return_value=2) as mock_store,
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as c:
                resp = await c.get("/api/brightdata/status/snap-abc")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ready"
        assert data["jobs_found"] == 2
        mock_store.assert_called_once()

    @pytest.mark.asyncio
    async def test_status_no_api_key(self):
        from app.main import app

        with patch(_SETTINGS_PATCH, return_value=_mock_settings(api_key="")):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as c:
                resp = await c.get("/api/brightdata/status/snap-abc")
        assert resp.status_code == 503

    @pytest.mark.asyncio
    async def test_status_api_error(self):
        from app.main import app

        mock_client = _mock_client(
            get_snapshot_status=AsyncMock(side_effect=BrightDataAPIError(404, "not found")),
        )

        with (
            patch(_SETTINGS_PATCH, return_value=_mock_settings()),
            patch(_CLIENT_PATCH, return_value=mock_client),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as c:
                resp = await c.get("/api/brightdata/status/snap-bad")
        assert resp.status_code == 502


class TestPrecrawl:
    @pytest.mark.asyncio
    async def test_precrawl_success(self):
        from app.main import app

        with (
            patch(_SETTINGS_PATCH, return_value=_mock_settings()),
            patch(_PRECRAWL_PATCH, new_callable=AsyncMock, return_value={
                "snapshot_id": "snap-pre", "jobs_cached": 15, "skipped": False,
            }),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as c:
                resp = await c.post("/api/brightdata/precrawl")
        assert resp.status_code == 200
        data = resp.json()
        assert data["jobs_cached"] == 15

    @pytest.mark.asyncio
    async def test_precrawl_no_api_key(self):
        from app.main import app

        with patch(_SETTINGS_PATCH, return_value=_mock_settings(api_key="")):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as c:
                resp = await c.post("/api/brightdata/precrawl")
        assert resp.status_code == 503



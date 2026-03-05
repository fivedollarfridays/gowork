"""Tests for BrightData polling with exponential backoff."""

from unittest.mock import AsyncMock, patch

import pytest

from app.integrations.brightdata.client import BrightDataClient
from app.integrations.brightdata.polling import poll_until_ready
from app.integrations.brightdata.types import (
    BrightDataAPIError,
    BrightDataTimeoutError,
    CrawlProgress,
    CrawlResult,
    CrawlStatus,
)

_SLEEP_PATCH = "app.integrations.brightdata.polling.asyncio.sleep"


def _make_client() -> BrightDataClient:
    return BrightDataClient(api_key="key-123", dataset_id="ds-123")


def _progress(pct: float | None = None) -> CrawlProgress:
    return CrawlProgress(snapshot_id="snap-1", status=CrawlStatus.RUNNING, progress_pct=pct)


def _result(jobs: list[dict] | None = None) -> CrawlResult:
    return CrawlResult(snapshot_id="snap-1", jobs=jobs or [{"title": "Test Job"}])


class TestPollUntilReady:
    @pytest.mark.asyncio
    async def test_returns_immediately_when_ready(self):
        """First poll returns CrawlResult — no retries needed."""
        client = _make_client()
        with (
            patch.object(client, "get_snapshot_status", new_callable=AsyncMock, return_value=_result()),
            patch(_SLEEP_PATCH, new_callable=AsyncMock) as mock_sleep,
        ):
            result = await poll_until_ready(client, "snap-1")
        assert isinstance(result, CrawlResult)
        assert len(result.jobs) == 1
        mock_sleep.assert_not_called()

    @pytest.mark.asyncio
    async def test_retries_until_ready(self):
        """Polls running twice, then returns ready result."""
        client = _make_client()
        side_effects = [_progress(0.3), _progress(0.7), _result()]
        with (
            patch.object(client, "get_snapshot_status", new_callable=AsyncMock, side_effect=side_effects),
            patch(_SLEEP_PATCH, new_callable=AsyncMock) as mock_sleep,
        ):
            result = await poll_until_ready(client, "snap-1")
        assert isinstance(result, CrawlResult)
        assert mock_sleep.call_count == 2

    @pytest.mark.asyncio
    async def test_raises_timeout_after_max_retries(self):
        """Exceeding max_retries raises BrightDataTimeoutError."""
        client = _make_client()
        with (
            patch.object(client, "get_snapshot_status", new_callable=AsyncMock, return_value=_progress()),
            patch(_SLEEP_PATCH, new_callable=AsyncMock),
        ):
            with pytest.raises(BrightDataTimeoutError):
                await poll_until_ready(client, "snap-1", max_retries=3)

    @pytest.mark.asyncio
    async def test_raises_on_failed_status(self):
        """FAILED status raises BrightDataAPIError."""
        client = _make_client()
        failed = CrawlProgress(snapshot_id="snap-1", status=CrawlStatus.FAILED)
        with (
            patch.object(client, "get_snapshot_status", new_callable=AsyncMock, return_value=failed),
            patch(_SLEEP_PATCH, new_callable=AsyncMock),
        ):
            with pytest.raises(BrightDataAPIError):
                await poll_until_ready(client, "snap-1")

    @pytest.mark.asyncio
    async def test_backoff_increases_delay(self):
        """Delay should increase with each retry (exponential backoff)."""
        client = _make_client()
        side_effects = [_progress(), _progress(), _result()]
        with (
            patch.object(client, "get_snapshot_status", new_callable=AsyncMock, side_effect=side_effects),
            patch(_SLEEP_PATCH, new_callable=AsyncMock) as mock_sleep,
        ):
            await poll_until_ready(client, "snap-1", base_delay=1.0, max_delay=60.0)
        delays = [call.args[0] for call in mock_sleep.call_args_list]
        assert len(delays) == 2
        # Second delay should be >= first (exponential growth + jitter)
        # base_delay * 2^0 + jitter, base_delay * 2^1 + jitter
        assert delays[0] >= 1.0  # min is base_delay * 2^0
        assert delays[1] >= 2.0  # min is base_delay * 2^1

    @pytest.mark.asyncio
    async def test_delay_capped_at_max(self):
        """Delay should never exceed max_delay + jitter (jitter < 1)."""
        client = _make_client()
        side_effects = [_progress()] * 5 + [_result()]
        with (
            patch.object(client, "get_snapshot_status", new_callable=AsyncMock, side_effect=side_effects),
            patch(_SLEEP_PATCH, new_callable=AsyncMock) as mock_sleep,
        ):
            await poll_until_ready(client, "snap-1", base_delay=1.0, max_delay=5.0, max_retries=10)
        delays = [call.args[0] for call in mock_sleep.call_args_list]
        # All delays should be < max_delay + 1 (jitter bound)
        assert all(d < 6.0 for d in delays)

    @pytest.mark.asyncio
    async def test_custom_max_retries(self):
        """Configurable max_retries works."""
        client = _make_client()
        with (
            patch.object(client, "get_snapshot_status", new_callable=AsyncMock, return_value=_progress()),
            patch(_SLEEP_PATCH, new_callable=AsyncMock) as mock_sleep,
        ):
            with pytest.raises(BrightDataTimeoutError):
                await poll_until_ready(client, "snap-1", max_retries=2)
        assert mock_sleep.call_count == 2

"""T13.92 — Outbound HTTP timeout & retry behavior tests.

Verifies that:
  * Every backend httpx call site has an explicit ``timeout=`` argument.
  * Idempotent GET helpers retry with exponential backoff on connection
    errors and 5xx responses.
  * Non-idempotent POST/PATCH/DELETE call sites do NOT silently retry.
  * 4xx responses are surfaced on the first attempt (no retry).

Tests are organized per-integration so a regression in any single
adapter is easy to localize.
"""

from __future__ import annotations

import inspect
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.integrations._http_retry import async_get_with_retry, NoRetry5xxError
from app.integrations.adapters import twc_adapter, usajobs_adapter
from app.integrations.brightdata.client import BrightDataClient
from app.integrations.brightdata.types import (
    BrightDataAPIError,
    CrawlResult,
    CrawlStatus,
)
from app.routes import credit as credit_route


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def _resp(status: int, *, json=None, text: str | None = None) -> httpx.Response:
    """Build an httpx.Response stand-in attached to a dummy request.

    Pass ``json=`` for a JSON body, ``text=`` for a plaintext body. We
    must only pass one — httpx's ``text=`` overrides ``json=`` even
    when empty.
    """
    kwargs: dict = {"request": httpx.Request("GET", "https://example.com")}
    if text is not None:
        kwargs["text"] = text
    elif json is not None:
        kwargs["json"] = json
    else:
        kwargs["json"] = {}
    return httpx.Response(status, **kwargs)


# --------------------------------------------------------------------------- #
# Cycle 1 — _http_retry helper
# --------------------------------------------------------------------------- #


class TestHttpRetryHelper:
    """The retry helper used by idempotent GET call sites."""

    @pytest.mark.asyncio
    async def test_returns_response_on_first_success(self):
        """A 200 on the first attempt should not retry."""
        client = AsyncMock()
        client.get = AsyncMock(return_value=_resp(200, json={"ok": True}))
        result = await async_get_with_retry(client, "https://x")
        assert result.status_code == 200
        assert client.get.await_count == 1

    @pytest.mark.asyncio
    async def test_retries_on_5xx_then_succeeds(self):
        """A 503 on attempt 1 followed by 200 on attempt 2 should succeed."""
        client = AsyncMock()
        client.get = AsyncMock(
            side_effect=[_resp(503), _resp(200, json={"ok": True})],
        )
        result = await async_get_with_retry(
            client, "https://x", base_delay=0.0, max_attempts=3,
        )
        assert result.status_code == 200
        assert client.get.await_count == 2

    @pytest.mark.asyncio
    async def test_does_not_retry_on_4xx(self):
        """A 404 should be returned immediately — no retry."""
        client = AsyncMock()
        client.get = AsyncMock(return_value=_resp(404))
        result = await async_get_with_retry(
            client, "https://x", base_delay=0.0, max_attempts=3,
        )
        assert result.status_code == 404
        assert client.get.await_count == 1

    @pytest.mark.asyncio
    async def test_retries_on_connect_error_then_succeeds(self):
        """A ConnectError on attempt 1 followed by 200 should succeed."""
        client = AsyncMock()
        client.get = AsyncMock(
            side_effect=[
                httpx.ConnectError("refused"),
                _resp(200, json={"ok": True}),
            ],
        )
        result = await async_get_with_retry(
            client, "https://x", base_delay=0.0, max_attempts=3,
        )
        assert result.status_code == 200
        assert client.get.await_count == 2

    @pytest.mark.asyncio
    async def test_gives_up_after_max_attempts_on_5xx(self):
        """Persistent 5xx should raise NoRetry5xxError after max_attempts."""
        client = AsyncMock()
        client.get = AsyncMock(return_value=_resp(503))
        with pytest.raises(NoRetry5xxError):
            await async_get_with_retry(
                client, "https://x", base_delay=0.0, max_attempts=3,
            )
        assert client.get.await_count == 3


# --------------------------------------------------------------------------- #
# Cycle 2 — BrightData (POST trigger + GET status)
# --------------------------------------------------------------------------- #


class TestBrightDataTimeoutAndRetry:
    """BrightData has POST (trigger) and GET (snapshot status)."""

    def test_brightdata_client_has_explicit_timeout(self):
        client = BrightDataClient(api_key="k", dataset_id="d")
        assert client._http.timeout is not None
        # connect/read/write/pool should all be set, not None
        timeout = client._http.timeout
        assert timeout.read is not None and timeout.read > 0
        assert timeout.connect is not None and timeout.connect > 0

    @pytest.mark.asyncio
    async def test_brightdata_get_retries_on_5xx(self):
        """get_snapshot_status should retry GETs that return 5xx."""
        client = BrightDataClient(api_key="k", dataset_id="d")
        responses = [
            _resp(503),
            _resp(200, json=[{"id": "j1"}]),
        ]
        with patch.object(
            client._http, "get", new_callable=AsyncMock, side_effect=responses,
        ) as mock_get:
            result = await client.get_snapshot_status("snap-1")
        assert isinstance(result, CrawlResult)
        assert result.snapshot_id == "snap-1"
        assert mock_get.await_count == 2

    @pytest.mark.asyncio
    async def test_brightdata_get_does_not_retry_on_4xx(self):
        """A 404 from snapshot status should surface on first attempt."""
        client = BrightDataClient(api_key="k", dataset_id="d")
        with patch.object(
            client._http,
            "get",
            new_callable=AsyncMock,
            return_value=_resp(404, text="not found"),
        ) as mock_get:
            with pytest.raises(BrightDataAPIError) as exc:
                await client.get_snapshot_status("snap-missing")
        assert exc.value.status_code == 404
        assert mock_get.await_count == 1

    @pytest.mark.asyncio
    async def test_brightdata_post_does_not_silently_retry_on_5xx(self):
        """trigger_crawl is non-idempotent — surface 5xx, do not retry."""
        client = BrightDataClient(api_key="k", dataset_id="d")
        with patch.object(
            client._http,
            "post",
            new_callable=AsyncMock,
            return_value=_resp(503, text="server error"),
        ) as mock_post:
            with pytest.raises(BrightDataAPIError) as exc:
                await client.trigger_crawl(["https://indeed.com/jobs"])
        assert exc.value.status_code == 503
        assert mock_post.await_count == 1


# --------------------------------------------------------------------------- #
# Cycle 3 — USAJobs adapter
# --------------------------------------------------------------------------- #


class TestUsajobsTimeoutAndRetry:
    """USAJobs is GET-only and idempotent."""

    def test_usajobs_has_explicit_timeout_constant(self):
        assert hasattr(usajobs_adapter, "_TIMEOUT")
        assert usajobs_adapter._TIMEOUT > 0

    @pytest.mark.asyncio
    async def test_usajobs_get_retries_on_5xx(self, monkeypatch):
        """USAJobs GET should retry once on 5xx then succeed."""
        monkeypatch.setenv("USAJOBS_API_KEY", "test-key")
        monkeypatch.setenv("USAJOBS_EMAIL", "test@example.com")
        responses = [
            _resp(503),
            _resp(
                200,
                json={
                    "SearchResult": {
                        "SearchResultItems": [
                            {"MatchedObjectDescriptor": {"PositionTitle": "Analyst"}},
                        ],
                    },
                },
            ),
        ]
        instance = AsyncMock()
        instance.get = AsyncMock(side_effect=responses)
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=False)
        with patch(
            "app.integrations.adapters.usajobs_adapter.httpx.AsyncClient",
            return_value=instance,
        ):
            result = await usajobs_adapter._fetch_usajobs("dev", "Austin")
        assert len(result) == 1
        assert result[0]["title"] == "Analyst"
        assert instance.get.await_count == 2

    @pytest.mark.asyncio
    async def test_usajobs_get_does_not_retry_on_4xx(self, monkeypatch):
        """A 404 should propagate on the first attempt (no retry)."""
        monkeypatch.setenv("USAJOBS_API_KEY", "test-key")
        monkeypatch.setenv("USAJOBS_EMAIL", "test@example.com")
        instance = AsyncMock()
        instance.get = AsyncMock(return_value=_resp(404, text="not found"))
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=False)
        with patch(
            "app.integrations.adapters.usajobs_adapter.httpx.AsyncClient",
            return_value=instance,
        ):
            with pytest.raises(httpx.HTTPStatusError):
                await usajobs_adapter._fetch_usajobs("dev", "Austin")
        assert instance.get.await_count == 1


# --------------------------------------------------------------------------- #
# Cycle 4 — TWC adapter
# --------------------------------------------------------------------------- #


class TestTwcTimeoutAndRetry:
    """TWC is GET-only and idempotent."""

    def test_twc_has_explicit_timeout_constant(self):
        assert hasattr(twc_adapter, "_TIMEOUT")
        assert twc_adapter._TIMEOUT > 0

    @pytest.mark.asyncio
    async def test_twc_get_retries_on_5xx(self):
        """TWC GET should retry once on 5xx then succeed."""
        responses = [
            _resp(502),
            _resp(200, json=[{"title": "Welder", "company": "Acme"}]),
        ]
        instance = AsyncMock()
        instance.get = AsyncMock(side_effect=responses)
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=False)
        with patch(
            "app.integrations.adapters.twc_adapter.httpx.AsyncClient",
            return_value=instance,
        ):
            result = await twc_adapter._fetch_twc_jobs("welder", "Houston")
        assert len(result) == 1
        assert result[0]["title"] == "Welder"
        assert instance.get.await_count == 2

    @pytest.mark.asyncio
    async def test_twc_get_does_not_retry_on_4xx(self):
        """403 from TWC should not retry."""
        instance = AsyncMock()
        instance.get = AsyncMock(return_value=_resp(403, text="forbidden"))
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=False)
        with patch(
            "app.integrations.adapters.twc_adapter.httpx.AsyncClient",
            return_value=instance,
        ):
            with pytest.raises(httpx.HTTPStatusError):
                await twc_adapter._fetch_twc_jobs("welder", "Houston")
        assert instance.get.await_count == 1


# --------------------------------------------------------------------------- #
# Cycle 5 — Credit microservice (POST, non-idempotent)
# --------------------------------------------------------------------------- #


class TestCreditTimeoutAndRetry:
    """Credit POST is non-idempotent; must NOT silently retry."""

    def test_credit_route_uses_timeout(self):
        """The credit route must set ``timeout=`` on its httpx client.

        We assert by inspecting the source of ``assess_credit`` because
        the actual client is constructed at request time inside the
        function. A regression that drops the timeout would be visible
        here.
        """
        src = inspect.getsource(credit_route.assess_credit)
        assert "timeout=" in src, "credit route must pass explicit timeout="

    @pytest.mark.anyio
    async def test_credit_post_does_not_silently_retry_on_5xx(self, client):
        """A 503 from the credit microservice should surface (no retry)."""
        valid_payload = {
            "credit_score": 580,
            "utilization_percent": 45.0,
            "total_accounts": 5,
            "open_accounts": 3,
            "payment_history_percent": 85.0,
            "oldest_account_months": 24,
        }
        mock_resp = AsyncMock()
        mock_resp.status_code = 503
        mock_resp.json.return_value = {"detail": "upstream busy"}
        mock_resp.text = "upstream busy"

        instance = AsyncMock()
        instance.post = AsyncMock(return_value=mock_resp)
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "app.routes.credit.httpx.AsyncClient", return_value=instance,
        ):
            resp = await client.post("/api/credit/assess", json=valid_payload)
        # 503 from upstream should be surfaced as 502 by the proxy on
        # the very first attempt — no silent retry.
        assert resp.status_code == 502
        assert instance.post.await_count == 1

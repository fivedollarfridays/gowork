"""Tests for shared RateLimiter class."""

import time
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.rate_limit import RateLimiter
from app.main import app


class TestRateLimiter:
    def test_allows_under_limit(self):
        """Requests under max are allowed."""
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        for _ in range(5):
            assert limiter.check("1.2.3.4") is True

    def test_blocks_over_limit(self):
        """Request exceeding max is blocked."""
        limiter = RateLimiter(max_requests=3, window_seconds=60)
        for _ in range(3):
            limiter.check("1.2.3.4")
        assert limiter.check("1.2.3.4") is False

    def test_per_key_isolation(self):
        """Different keys have independent limits."""
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        limiter.check("a")
        limiter.check("a")
        assert limiter.check("a") is False
        assert limiter.check("b") is True

    def test_window_expiry(self):
        """Old requests outside window don't count."""
        limiter = RateLimiter(max_requests=2, window_seconds=10)
        limiter.check("x")
        limiter.check("x")
        assert limiter.check("x") is False

        with patch("app.core.rate_limit.time") as mock_time:
            mock_time.monotonic.return_value = time.monotonic() + 11
            assert limiter.check("x") is True

    def test_clear_resets(self):
        """Clear removes all tracked requests."""
        limiter = RateLimiter(max_requests=1, window_seconds=60)
        limiter.check("k")
        assert limiter.check("k") is False
        limiter.clear()
        assert limiter.check("k") is True

    def test_prune_stale_keys_at_100_calls(self):
        """Every 100 successful checks, stale keys are pruned."""
        limiter = RateLimiter(max_requests=200, window_seconds=1)
        # Make 99 successful checks to get _call_count to 99
        for _ in range(99):
            assert limiter.check("key1") is True
        # Inject a stale key with timestamp 0 (always expired)
        limiter._requests["stale_key"] = [0.0]
        assert "stale_key" in limiter._requests
        # 100th check triggers _prune_stale via _call_count % 100 == 0
        assert limiter.check("key1") is True
        assert "stale_key" not in limiter._requests


_VALID_UUID = "00000000-0000-4000-8000-000000000001"
_GET_SESSION = "app.routes.plan.get_session_by_id"
_GENERATE = "app.routes.plan.generate_narrative"
_UPDATE = "app.routes.plan.update_session_plan"


class TestPlanGenerateRateLimit:
    """POST /api/plan/{id}/generate is rate limited."""

    @pytest.mark.asyncio
    async def test_generate_rate_limited(self):
        from app.ai.types import PlanNarrative
        from app.routes.plan import _rate_limiter

        _rate_limiter.clear()
        row = {
            "id": _VALID_UUID,
            "created_at": "2026-03-05T12:00:00+00:00",
            "barriers": '["credit"]',
            "credit_profile": None,
            "qualifications": "CNA",
            "plan": '{"plan_id": "p1", "barriers": []}',
            "expires_at": "2026-03-06T12:00:00+00:00",
        }
        narrative = PlanNarrative(summary="test", key_actions=["a"])

        with (
            patch(_GET_SESSION, new_callable=AsyncMock, return_value=row),
            patch(_GENERATE, new_callable=AsyncMock, return_value=narrative),
            patch(_UPDATE, new_callable=AsyncMock),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                # Send 5 requests (the limit)
                for _ in range(5):
                    await client.post(f"/api/plan/{_VALID_UUID}/generate")
                # 6th should be blocked
                resp = await client.post(f"/api/plan/{_VALID_UUID}/generate")
        assert resp.status_code == 429
        _rate_limiter.clear()


class TestCreditAssessRateLimit:
    """POST /api/credit/assess is rate limited."""

    @pytest.mark.asyncio
    async def test_credit_rate_limited(self):
        from app.routes.credit import _rate_limiter

        _rate_limiter.clear()

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Send 10 requests (the limit) — they'll fail with 503 but still count
            for _ in range(10):
                await client.post("/api/credit/assess", json={
                    "credit_score": 620,
                    "utilization_percent": 30.0,
                    "total_accounts": 5,
                    "open_accounts": 3,
                    "negative_items": [],
                    "payment_history_percent": 90.0,
                    "oldest_account_months": 24,
                })
            # 11th should be rate limited
            resp = await client.post("/api/credit/assess", json={
                "credit_score": 620,
                "utilization_percent": 30.0,
                "total_accounts": 5,
                "open_accounts": 3,
                "negative_items": [],
                "payment_history_percent": 90.0,
                "oldest_account_months": 24,
            })
        assert resp.status_code == 429
        _rate_limiter.clear()

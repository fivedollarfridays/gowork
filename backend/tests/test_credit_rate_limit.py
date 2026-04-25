"""Per-session rate limiting on the credit assessment proxy (T13.99).

``POST /api/credit/assess`` proxies to an outbound credit microservice.
Without a tight rate limit, a single caller can burn outbound API cost
*and* eat into the upstream's per-tenant quota. The audit (T13.99 HIGH)
flags this alongside the documents endpoints.

Limit: ``RateLimiter(max_requests=5, window_seconds=60)`` — same value
as ``routes/plan.py`` because both endpoints are similarly expensive
(LLM call vs. external paid API).

Note on keying
--------------
``SimpleCreditRequest`` carries no ``session_id`` field, so the limiter
keys by client IP — the closest available "per-session" axis without
changing the public API contract. The route does not own a token, so
session_id-based keying would require a contract change. This file
documents that decision: if/when ``SimpleCreditRequest`` gains a
``session_id`` field, the limiter and these tests should switch.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.routes.credit import _credit_rate_limiter

VALID_PAYLOAD = {
    "credit_score": 620,
    "utilization_percent": 30.0,
    "total_accounts": 5,
    "open_accounts": 3,
    "negative_items": [],
    "payment_history_percent": 90.0,
    "oldest_account_months": 24,
}

_FULL_OK_RESPONSE = {
    "barrier_severity": "low",
    "barrier_details": [],
    "readiness": {"score": 70, "fico_score": 620, "score_band": "fair"},
    "thresholds": [],
    "dispute_pathway": {"steps": [], "total_estimated_days": 0},
    "eligibility": [],
    "disclaimer": "info",
}


@pytest.fixture(autouse=True)
def _clear_credit_limiter():
    _credit_rate_limiter.clear()
    yield
    _credit_rate_limiter.clear()


def _mock_async_client(mock_cls: MagicMock) -> None:
    """Wire ``httpx.AsyncClient`` to return a 200 success."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = _FULL_OK_RESPONSE
    instance = AsyncMock()
    instance.post.return_value = mock_resp
    instance.__aenter__ = AsyncMock(return_value=instance)
    instance.__aexit__ = AsyncMock(return_value=False)
    mock_cls.return_value = instance


@pytest.mark.anyio
async def test_credit_endpoint_rate_limited():
    """Sixth credit-assess POST in the same window must return 429.

    Five rapid POSTs from one IP should succeed; the sixth must be
    rejected with 429. The mocked outbound call returns a 200 every
    time so the test isolates the limiter's behaviour from upstream
    error handling.
    """
    with patch("app.routes.credit.httpx.AsyncClient") as mock_cls:
        _mock_async_client(mock_cls)
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test",
        ) as client:
            for i in range(5):
                resp = await client.post(
                    "/api/credit/assess", json=VALID_PAYLOAD,
                )
                assert resp.status_code == 200, (
                    f"call #{i + 1} unexpectedly failed: {resp.text}"
                )
            # 6th must be denied.
            resp = await client.post(
                "/api/credit/assess", json=VALID_PAYLOAD,
            )
            assert resp.status_code == 429, resp.text

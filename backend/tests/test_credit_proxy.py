"""Tests for credit proxy — error handling and success path."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.routes.credit import _rate_limiter


@pytest.fixture(autouse=True)
def _clear_credit_rate_limiter():
    _rate_limiter.clear()
    yield
    _rate_limiter.clear()

FULL_CREDIT_RESPONSE = {
    "barrier_severity": "medium",
    "barrier_details": [{"severity": "medium", "description": "test"}],
    "readiness": {"score": 45, "fico_score": 580, "score_band": "poor"},
    "thresholds": [{"threshold_name": "fair", "threshold_score": 650}],
    "dispute_pathway": {"steps": [], "total_estimated_days": 90},
    "eligibility": [{"product_name": "auto loan", "status": "not_eligible"}],
    "disclaimer": "This is not financial advice.",
}

VALID_PAYLOAD = {
    "credit_score": 580,
    "utilization_percent": 45.0,
    "total_accounts": 5,
    "open_accounts": 3,
    "payment_history_percent": 85.0,
    "oldest_account_months": 24,
}


def _mock_httpx_client(mock_cls, *, side_effect=None, return_value=None):
    """Wire up a mock httpx.AsyncClient context manager."""
    instance = AsyncMock()
    if side_effect:
        instance.post.side_effect = side_effect
    else:
        instance.post.return_value = return_value
    instance.__aenter__ = AsyncMock(return_value=instance)
    instance.__aexit__ = AsyncMock(return_value=False)
    mock_cls.return_value = instance


class TestCreditProxyErrors:
    @pytest.mark.anyio
    async def test_connect_error_returns_503(self, client):
        """ConnectError should return 503."""
        with patch("app.routes.credit.httpx.AsyncClient") as mock_cls:
            _mock_httpx_client(mock_cls, side_effect=httpx.ConnectError("refused"))
            resp = await client.post("/api/credit/assess", json=VALID_PAYLOAD)
            assert resp.status_code == 503
            assert "unavailable" in resp.json()["detail"].lower()

    @pytest.mark.anyio
    async def test_timeout_returns_504(self, client):
        """TimeoutException should return 504."""
        with patch("app.routes.credit.httpx.AsyncClient") as mock_cls:
            _mock_httpx_client(mock_cls, side_effect=httpx.TimeoutException("timed out"))
            resp = await client.post("/api/credit/assess", json=VALID_PAYLOAD)
            assert resp.status_code == 504
            assert "timed out" in resp.json()["detail"].lower()

    @pytest.mark.anyio
    async def test_non_json_error_response(self, client):
        """Non-JSON error body should not cause 500."""
        mock_resp = AsyncMock()
        mock_resp.status_code = 502
        mock_resp.json.side_effect = Exception("not JSON")
        mock_resp.text = "<html>Bad Gateway</html>"

        with patch("app.routes.credit.httpx.AsyncClient") as mock_cls:
            _mock_httpx_client(mock_cls, return_value=mock_resp)
            resp = await client.post("/api/credit/assess", json=VALID_PAYLOAD)
            assert resp.status_code == 502

    @pytest.mark.anyio
    async def test_other_network_error_returns_502(self, client):
        """Other httpx errors (ReadError, etc.) should return 502."""
        with patch("app.routes.credit.httpx.AsyncClient") as mock_cls:
            _mock_httpx_client(mock_cls, side_effect=httpx.ReadError("connection reset"))
            resp = await client.post("/api/credit/assess", json=VALID_PAYLOAD)
            assert resp.status_code == 502
            assert "network error" in resp.json()["detail"].lower()


class TestCreditProxySuccess:
    @pytest.mark.anyio
    async def test_success_returns_api_response(self, client):
        """200 from credit API should pass through the response body."""
        credit_response = {
            "barrier_severity": "medium",
            "barrier_details": [{"type": "utilization", "severity": "medium"}],
            "readiness": {"score": 45, "fico_score": 580, "score_band": "poor"},
            "thresholds": [{"threshold_name": "fair", "threshold_score": 650}],
            "dispute_pathway": {"steps": [], "total_estimated_days": 90},
            "eligibility": [{"product_name": "auto loan", "status": "not_eligible"}],
            "disclaimer": "This is not financial advice.",
        }
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = credit_response

        with patch("app.routes.credit.httpx.AsyncClient") as mock_cls:
            _mock_httpx_client(mock_cls, return_value=mock_resp)
            resp = await client.post("/api/credit/assess", json=VALID_PAYLOAD)
            assert resp.status_code == 200
            assert resp.json() == credit_response

    @pytest.mark.anyio
    async def test_calls_simple_endpoint(self, client):
        """Proxy should call /v1/assess/simple, not /v1/assess."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = FULL_CREDIT_RESPONSE

        with patch("app.routes.credit.httpx.AsyncClient") as mock_cls:
            instance = AsyncMock()
            instance.post.return_value = mock_resp
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = instance

            await client.post("/api/credit/assess", json=VALID_PAYLOAD)

            call_url = instance.post.call_args[0][0]
            assert "/v1/assess/simple" in call_url

    @pytest.mark.anyio
    async def test_payload_sent_directly_no_score_band(self, client):
        """Payload should be sent as-is — no score_band injected."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = FULL_CREDIT_RESPONSE

        with patch("app.routes.credit.httpx.AsyncClient") as mock_cls:
            instance = AsyncMock()
            instance.post.return_value = mock_resp
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = instance

            await client.post("/api/credit/assess", json=VALID_PAYLOAD)

            sent_json = instance.post.call_args[1]["json"]
            assert "score_band" not in sent_json
            assert "account_summary" not in sent_json
            assert sent_json["credit_score"] == 580

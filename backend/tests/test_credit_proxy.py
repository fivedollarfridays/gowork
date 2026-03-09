"""Tests for credit proxy — error handling and success path."""

import logging
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
        """Non-JSON error body should return generic 502."""
        mock_resp = AsyncMock()
        mock_resp.status_code = 502
        mock_resp.json.side_effect = Exception("not JSON")
        mock_resp.text = "<html>Bad Gateway</html>"

        with patch("app.routes.credit.httpx.AsyncClient") as mock_cls:
            _mock_httpx_client(mock_cls, return_value=mock_resp)
            resp = await client.post("/api/credit/assess", json=VALID_PAYLOAD)
            assert resp.status_code == 502
            assert "Bad Gateway" not in resp.json()["detail"]

    @pytest.mark.anyio
    async def test_other_network_error_returns_502(self, client):
        """Other httpx errors (ReadError, etc.) should return 502."""
        with patch("app.routes.credit.httpx.AsyncClient") as mock_cls:
            _mock_httpx_client(mock_cls, side_effect=httpx.ReadError("connection reset"))
            resp = await client.post("/api/credit/assess", json=VALID_PAYLOAD)
            assert resp.status_code == 502
            assert "network error" in resp.json()["detail"].lower()


class TestCreditProxyErrorMasking:
    @pytest.mark.anyio
    async def test_upstream_detail_not_forwarded(self, client):
        """Upstream error detail must not be exposed to client."""
        mock_resp = MagicMock()
        mock_resp.status_code = 422
        mock_resp.json.return_value = {"detail": "SSN format invalid — expected XXX-XX-XXXX"}
        mock_resp.text = '{"detail": "SSN format invalid"}'

        with patch("app.routes.credit.httpx.AsyncClient") as mock_cls:
            _mock_httpx_client(mock_cls, return_value=mock_resp)
            resp = await client.post("/api/credit/assess", json=VALID_PAYLOAD)
            assert resp.status_code == 502
            body = resp.json()["detail"]
            assert "SSN" not in body
            assert "credit assessment" in body.lower()

    @pytest.mark.anyio
    async def test_connect_error_no_port_info(self, client):
        """ConnectError message must not reveal port or host."""
        with patch("app.routes.credit.httpx.AsyncClient") as mock_cls:
            _mock_httpx_client(mock_cls, side_effect=httpx.ConnectError("Connection refused on port 8001"))
            resp = await client.post("/api/credit/assess", json=VALID_PAYLOAD)
            detail = resp.json()["detail"]
            assert "8001" not in detail
            assert "port" not in detail.lower()

    @pytest.mark.anyio
    async def test_upstream_error_logged_server_side(self, client, caplog):
        """Upstream error detail should be logged at WARNING level."""
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.json.return_value = {"detail": "internal db crash"}
        mock_resp.text = '{"detail": "internal db crash"}'

        with patch("app.routes.credit.httpx.AsyncClient") as mock_cls:
            _mock_httpx_client(mock_cls, return_value=mock_resp)
            with caplog.at_level(logging.WARNING, logger="app.routes.credit"):
                await client.post("/api/credit/assess", json=VALID_PAYLOAD)
            assert any("500" in r.message for r in caplog.records)


class TestCreditApiUrlValidation:
    def test_rejects_private_ip_in_production(self):
        """credit_api_url must reject RFC 1918 addresses in production."""
        from app.core.config import Settings

        with pytest.raises(Exception):
            Settings(
                environment="production",
                credit_api_url="http://192.168.1.1:8001",
                cors_origins="https://app.example.com",
            )

    def test_rejects_localhost_in_production(self):
        """credit_api_url must reject localhost in production."""
        from app.core.config import Settings

        with pytest.raises(Exception):
            Settings(
                environment="production",
                credit_api_url="http://127.0.0.1:8001",
                cors_origins="https://app.example.com",
            )

    def test_rejects_link_local_in_production(self):
        """credit_api_url must reject link-local addresses in production."""
        from app.core.config import Settings

        with pytest.raises(Exception):
            Settings(
                environment="production",
                credit_api_url="http://169.254.1.1:8001",
                cors_origins="https://app.example.com",
            )

    def test_allows_private_ip_in_development(self):
        """credit_api_url can be private IP in development."""
        from app.core.config import Settings

        s = Settings(
            environment="development",
            credit_api_url="http://127.0.0.1:8001",
            cors_origins="http://localhost:3000",
        )
        assert s.credit_api_url == "http://127.0.0.1:8001"

    def test_allows_public_url_in_production(self):
        """credit_api_url can be a public URL in production."""
        from app.core.config import Settings

        s = Settings(
            environment="production",
            credit_api_url="https://credit-api.example.com",
            cors_origins="https://app.example.com",
            audit_hash_salt="test-production-salt-value",
            admin_api_key="a" * 32,
        )
        assert s.credit_api_url == "https://credit-api.example.com"


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

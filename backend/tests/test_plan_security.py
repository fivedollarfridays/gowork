"""Security tests for plan endpoints — token auth, input validation, info leak prevention."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.ai.client import generate_narrative
from app.core.config import Settings
from app.main import app

_VALID_UUID = "00000000-0000-4000-8000-000000000001"
_VALID_UUID_2 = "00000000-0000-4000-8000-000000000002"
_VALID_TOKEN = "tok-ok"
_WRONG_TOKEN = "tok-bad"

_GET_SESSION_PATCH = "app.routes.plan.get_session_by_id"
_VALIDATE_TOKEN_PATCH = "app.core.auth.validate_token"
_TOKEN_EXISTS_PATCH = "app.core.auth.token_exists"


def _seed_session_row(session_id=_VALID_UUID, with_plan=False):
    """Return a fake session row dict."""
    return {
        "id": session_id,
        "created_at": "2026-03-05T12:00:00+00:00",
        "barriers": json.dumps(["credit", "transportation"]),
        "credit_profile": None,
        "qualifications": "Former CNA at Baptist Hospital",
        "plan": json.dumps({"plan_id": "p1", "barriers": []}) if with_plan else None,
        "expires_at": "2026-03-06T12:00:00+00:00",
    }


# --- SEC-012: Path param validation ---

class TestSessionIdValidation:
    """Non-UUID session_id in path returns 422."""

    @pytest.mark.asyncio
    async def test_get_plan_rejects_non_uuid(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/plan/not-a-uuid")
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_generate_rejects_non_uuid(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/api/plan/not-a-uuid/generate")
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_career_center_rejects_non_uuid(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/plan/not-a-uuid/career-center")
        assert resp.status_code == 422


# --- SEC-017: Info leak prevention ---

class TestInfoLeakPrevention:
    @pytest.mark.asyncio
    async def test_invalid_json_logs_length_not_content(self):
        """Logger should log response length, not raw content."""
        raw_content = "Not JSON but contains sensitive data: SSN 123-45-6789"

        async def bad_stream(system_prompt, user_prompt):
            yield raw_content

        with (
            patch("app.ai.client.get_llm_stream", return_value=bad_stream("s", "u")),
            patch("app.ai.client.logger") as mock_logger,
        ):
            with pytest.raises(ValueError, match="invalid JSON"):
                await generate_narrative(
                    barriers=["credit"],
                    qualifications="CNA",
                    plan_data={"barriers": []},
                )
            log_call_args = str(mock_logger.warning.call_args)
            assert raw_content[:50] not in log_call_args
            assert str(len(raw_content)) in log_call_args


# --- SEC-004: Token-based session ownership ---


class TestPlanTokenAuth:
    """All plan endpoints require a valid feedback token matching the session."""

    @pytest.mark.asyncio
    async def test_get_plan_422_without_token(self):
        """GET /api/plan/{id} returns 422 when no token provided."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(f"/api/plan/{_VALID_UUID}")
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_get_plan_401_invalid_token(self):
        """GET /api/plan/{id} returns 401 for invalid/expired token."""
        row = _seed_session_row(with_plan=True)
        with (
            patch(_GET_SESSION_PATCH, new_callable=AsyncMock, return_value=row),
            patch(_VALIDATE_TOKEN_PATCH, new_callable=AsyncMock, return_value=None),
            patch(_TOKEN_EXISTS_PATCH, new_callable=AsyncMock, return_value=False),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get(f"/api/plan/{_VALID_UUID}?token={_WRONG_TOKEN}")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_get_plan_403_wrong_session(self):
        """GET /api/plan/{id} returns 403 when token belongs to a different session."""
        row = _seed_session_row(with_plan=True)
        with (
            patch(_GET_SESSION_PATCH, new_callable=AsyncMock, return_value=row),
            patch(_VALIDATE_TOKEN_PATCH, new_callable=AsyncMock, return_value="other-session-id"),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get(f"/api/plan/{_VALID_UUID}?token={_VALID_TOKEN}")
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_get_plan_200_valid_token(self):
        """GET /api/plan/{id} returns 200 with valid matching token."""
        row = _seed_session_row(with_plan=True)
        with (
            patch(_GET_SESSION_PATCH, new_callable=AsyncMock, return_value=row),
            patch(_VALIDATE_TOKEN_PATCH, new_callable=AsyncMock, return_value=_VALID_UUID),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get(f"/api/plan/{_VALID_UUID}?token={_VALID_TOKEN}")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_generate_requires_token(self):
        """POST /api/plan/{id}/generate returns 422 without token."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(f"/api/plan/{_VALID_UUID}/generate")
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_career_center_requires_token(self):
        """GET /api/plan/{id}/career-center returns 422 without token."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(f"/api/plan/{_VALID_UUID_2}/career-center")
        assert resp.status_code == 422


# --- Config: SSRF validator accepts public IPs in production ---

class TestConfigCreditUrlValidation:
    def test_production_with_public_ip_allowed(self):
        """Public IP in credit_api_url should pass production validation."""
        s = Settings(
            environment="production",
            credit_api_url="http://8.8.8.8:8001",
            audit_hash_salt="test-production-salt-value",
            admin_api_key="a" * 32,
        )
        assert s.credit_api_url == "http://8.8.8.8:8001"

"""Tests for plan route endpoints and AI client."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.ai.types import PlanNarrative


# --- Fixtures ---

def _seed_session_row(session_id="test-session-abc", with_plan=False):
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


_GET_SESSION_PATCH = "app.routes.plan.get_session_by_id"
_UPDATE_SESSION_PATCH = "app.routes.plan.update_session_plan"
_GENERATE_PATCH = "app.routes.plan.generate_narrative"
_FALLBACK_PATCH = "app.routes.plan.build_fallback_narrative"


# --- GET /api/plan/{session_id} ---

class TestGetPlan:
    @pytest.mark.asyncio
    async def test_valid_session_with_plan(self):
        """Returns stored plan for a valid session."""
        from app.main import app

        row = _seed_session_row(with_plan=True)
        with patch(_GET_SESSION_PATCH, new_callable=AsyncMock, return_value=row):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/plan/test-session-abc")
        assert resp.status_code == 200
        data = resp.json()
        assert data["session_id"] == "test-session-abc"
        assert data["plan"] is not None

    @pytest.mark.asyncio
    async def test_valid_session_no_plan(self):
        """Returns session with null plan when not yet generated."""
        from app.main import app

        row = _seed_session_row(with_plan=False)
        with patch(_GET_SESSION_PATCH, new_callable=AsyncMock, return_value=row):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/plan/test-session-abc")
        assert resp.status_code == 200
        data = resp.json()
        assert data["plan"] is None

    @pytest.mark.asyncio
    async def test_invalid_session_404(self):
        """Returns 404 for unknown session."""
        from app.main import app

        with patch(_GET_SESSION_PATCH, new_callable=AsyncMock, return_value=None):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/plan/nonexistent-id")
        assert resp.status_code == 404


# --- POST /api/plan/{session_id}/generate ---

class TestGeneratePlan:
    @pytest.mark.asyncio
    async def test_generates_narrative_success(self):
        """Generates AI narrative and stores it."""
        from app.main import app

        row = _seed_session_row(with_plan=True)
        narrative = PlanNarrative(
            summary="Monday morning, take Route 7 to the career center.",
            key_actions=["Visit career center", "Apply for CNA renewal"],
        )
        with (
            patch(_GET_SESSION_PATCH, new_callable=AsyncMock, return_value=row),
            patch(_GENERATE_PATCH, new_callable=AsyncMock, return_value=narrative),
            patch(_UPDATE_SESSION_PATCH, new_callable=AsyncMock),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.post("/api/plan/test-session-abc/generate")
        assert resp.status_code == 200
        data = resp.json()
        assert "summary" in data
        assert "key_actions" in data
        assert len(data["key_actions"]) == 2

    @pytest.mark.asyncio
    async def test_generate_404_for_missing_session(self):
        """Returns 404 when session does not exist."""
        from app.main import app

        with patch(_GET_SESSION_PATCH, new_callable=AsyncMock, return_value=None):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.post("/api/plan/nonexistent-id/generate")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_generate_requires_plan(self):
        """Returns 400 when session has no plan to narrate."""
        from app.main import app

        row = _seed_session_row(with_plan=False)
        with patch(_GET_SESSION_PATCH, new_callable=AsyncMock, return_value=row):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.post("/api/plan/test-session-abc/generate")
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_fallback_on_api_failure(self):
        """Falls back to template narrative when Claude API fails."""
        from app.main import app

        row = _seed_session_row(with_plan=True)
        fallback = PlanNarrative(
            summary="Based on your assessment, here are your next steps.",
            key_actions=["Visit Montgomery Career Center"],
        )
        with (
            patch(_GET_SESSION_PATCH, new_callable=AsyncMock, return_value=row),
            patch(_GENERATE_PATCH, new_callable=AsyncMock, side_effect=Exception("API down")),
            patch(_FALLBACK_PATCH, return_value=fallback),
            patch(_UPDATE_SESSION_PATCH, new_callable=AsyncMock),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.post("/api/plan/test-session-abc/generate")
        assert resp.status_code == 200
        data = resp.json()
        assert "next steps" in data["summary"]

    @pytest.mark.asyncio
    async def test_generate_corrupt_json_returns_500(self):
        """Returns 500 when session has corrupt JSON in barriers/plan."""
        from app.main import app

        row = _seed_session_row(with_plan=True)
        row["barriers"] = "not-json{{"
        with patch(_GET_SESSION_PATCH, new_callable=AsyncMock, return_value=row):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.post("/api/plan/test-session-abc/generate")
        assert resp.status_code == 500
        assert "Corrupt" in resp.json()["detail"]


# --- AI Client ---

class TestGetPlanCorruptData:
    @pytest.mark.asyncio
    async def test_corrupt_json_returns_500(self):
        """Returns 500 when session plan contains invalid JSON."""
        from app.main import app

        row = _seed_session_row(with_plan=False)
        row["plan"] = "not-valid-json{{"
        row["barriers"] = '["credit"]'
        with patch(_GET_SESSION_PATCH, new_callable=AsyncMock, return_value=row):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/plan/test-session-abc")
        assert resp.status_code == 500
        assert "Corrupt" in resp.json()["detail"]


class TestGenerateNarrative:
    @pytest.mark.asyncio
    async def test_calls_anthropic_and_parses(self):
        """generate_narrative calls Claude and returns PlanNarrative."""
        from app.ai.client import generate_narrative

        mock_message = MagicMock()
        mock_message.content = [MagicMock(text=json.dumps({
            "summary": "Take the Route 4 bus to JobLink.",
            "key_actions": ["Register at JobLink", "Get CNA license renewed"],
        }))]
        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_message)

        with patch("app.ai.client.AsyncAnthropic", return_value=mock_client):
            result = await generate_narrative(
                barriers=["credit", "transportation"],
                qualifications="Former CNA",
                plan_data={"barriers": [], "job_matches": []},
            )
        assert isinstance(result, PlanNarrative)
        assert "Route 4" in result.summary

    @pytest.mark.asyncio
    async def test_raises_on_invalid_json_from_claude(self):
        """generate_narrative raises ValueError when Claude returns bad JSON."""
        from app.ai.client import generate_narrative

        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="This is not JSON at all")]
        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_message)

        with patch("app.ai.client.AsyncAnthropic", return_value=mock_client):
            with pytest.raises(ValueError, match="invalid JSON"):
                await generate_narrative(
                    barriers=["credit"],
                    qualifications="CNA",
                    plan_data={"barriers": []},
                )

    @pytest.mark.asyncio
    async def test_raises_on_timeout(self):
        """generate_narrative raises on API timeout."""
        from anthropic import APITimeoutError
        from app.ai.client import generate_narrative

        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(
            side_effect=APITimeoutError(request=MagicMock())
        )

        with patch("app.ai.client.AsyncAnthropic", return_value=mock_client):
            with pytest.raises(APITimeoutError):
                await generate_narrative(
                    barriers=["credit"],
                    qualifications="Some work",
                    plan_data={"barriers": []},
                )


# --- Fallback ---

class TestBuildFallbackNarrative:
    def test_builds_from_plan_data(self):
        """Fallback produces structured narrative from plan data."""
        from app.ai.client import build_fallback_narrative

        plan_data = {
            "barriers": [
                {"type": "credit", "title": "Credit Repair", "actions": ["Check report"],
                 "resources": [{"name": "GreenPath Financial", "phone": "555-1234"}]},
            ],
            "job_matches": [{"title": "CNA", "company": "Baptist Hospital"}],
            "immediate_next_steps": ["Visit career center"],
        }
        result = build_fallback_narrative(
            barriers=["credit"],
            qualifications="Former CNA",
            plan_data=plan_data,
        )
        assert isinstance(result, PlanNarrative)
        assert len(result.summary) > 0
        assert len(result.key_actions) > 0

    def test_empty_plan_still_works(self):
        """Fallback handles empty plan gracefully."""
        from app.ai.client import build_fallback_narrative

        plan_data = {"barriers": [], "job_matches": [], "immediate_next_steps": []}
        result = build_fallback_narrative(
            barriers=[],
            qualifications="",
            plan_data=plan_data,
        )
        assert isinstance(result, PlanNarrative)
        assert len(result.summary) > 0

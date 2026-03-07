"""Tests for plan route endpoints and AI client."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.ai.client import build_fallback_narrative, generate_narrative
from app.ai.types import PlanNarrative
from app.main import app
from app.routes.plan import _rate_limiter


@pytest.fixture(autouse=True)
def _clear_plan_rate_limiter():
    _rate_limiter.clear()
    yield
    _rate_limiter.clear()


# --- Fixtures ---

_VALID_UUID = "00000000-0000-4000-8000-000000000001"
_VALID_UUID_2 = "00000000-0000-4000-8000-000000000002"
_MISSING_UUID = "00000000-0000-4000-8000-000000000099"


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


_GET_SESSION_PATCH = "app.routes.plan.get_session_by_id"
_UPDATE_SESSION_PATCH = "app.routes.plan.update_session_plan"
_GENERATE_PATCH = "app.routes.plan.generate_narrative"
_FALLBACK_PATCH = "app.routes.plan.build_fallback_narrative"


# --- GET /api/plan/{session_id} ---

class TestGetPlan:
    @pytest.mark.asyncio
    async def test_valid_session_with_plan(self):
        """Returns stored plan for a valid session."""
        row = _seed_session_row(with_plan=True)
        with patch(_GET_SESSION_PATCH, new_callable=AsyncMock, return_value=row):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get(f"/api/plan/{_VALID_UUID}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["session_id"] == _VALID_UUID
        assert data["plan"] is not None

    @pytest.mark.asyncio
    async def test_valid_session_no_plan(self):
        """Returns session with null plan when not yet generated."""
        row = _seed_session_row(with_plan=False)
        with patch(_GET_SESSION_PATCH, new_callable=AsyncMock, return_value=row):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get(f"/api/plan/{_VALID_UUID}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["plan"] is None

    @pytest.mark.asyncio
    async def test_invalid_session_404(self):
        """Returns 404 for unknown session."""
        with patch(_GET_SESSION_PATCH, new_callable=AsyncMock, return_value=None):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get(f"/api/plan/{_MISSING_UUID}")
        assert resp.status_code == 404


# --- POST /api/plan/{session_id}/generate ---

class TestGeneratePlan:
    @pytest.mark.asyncio
    async def test_generates_narrative_success(self):
        """Generates AI narrative and stores it."""
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
                resp = await client.post(f"/api/plan/{_VALID_UUID}/generate")
        assert resp.status_code == 200
        data = resp.json()
        assert "summary" in data
        assert "key_actions" in data
        assert len(data["key_actions"]) == 2

    @pytest.mark.asyncio
    async def test_generate_404_for_missing_session(self):
        """Returns 404 when session does not exist."""
        with patch(_GET_SESSION_PATCH, new_callable=AsyncMock, return_value=None):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.post(f"/api/plan/{_MISSING_UUID}/generate")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_generate_requires_plan(self):
        """Returns 400 when session has no plan to narrate."""
        row = _seed_session_row(with_plan=False)
        with patch(_GET_SESSION_PATCH, new_callable=AsyncMock, return_value=row):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.post(f"/api/plan/{_VALID_UUID}/generate")
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_fallback_on_api_failure(self):
        """Falls back to template narrative when Claude API fails."""
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
                resp = await client.post(f"/api/plan/{_VALID_UUID}/generate")
        assert resp.status_code == 200
        data = resp.json()
        assert "next steps" in data["summary"]

    @pytest.mark.asyncio
    async def test_fallback_runs_without_mock(self):
        """When Claude API fails, real fallback code runs and produces narrative."""
        row = _seed_session_row(with_plan=True)
        # Set plan with actual barrier data so fallback has something to work with
        row["plan"] = json.dumps({
            "barriers": [
                {"type": "credit", "title": "Credit Repair", "actions": ["Check report"],
                 "resources": [{"name": "GreenPath", "phone": "555-0100"}]},
            ],
            "job_matches": [{"title": "Warehouse Worker", "company": "Acme"}],
            "immediate_next_steps": ["Visit career center"],
        })
        with (
            patch(_GET_SESSION_PATCH, new_callable=AsyncMock, return_value=row),
            patch(_GENERATE_PATCH, new_callable=AsyncMock, side_effect=Exception("Claude down")),
            # DO NOT mock _FALLBACK_PATCH — let real fallback run
            patch(_UPDATE_SESSION_PATCH, new_callable=AsyncMock),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.post(f"/api/plan/{_VALID_UUID}/generate")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["summary"]) > 0
        assert len(data["key_actions"]) > 0

    @pytest.mark.asyncio
    async def test_double_fault_returns_500(self):
        """Returns 500 when both Claude API and fallback fail."""
        row = _seed_session_row(with_plan=True)
        with (
            patch(_GET_SESSION_PATCH, new_callable=AsyncMock, return_value=row),
            patch(_GENERATE_PATCH, new_callable=AsyncMock, side_effect=Exception("Claude down")),
            patch(_FALLBACK_PATCH, side_effect=RuntimeError("Fallback also broken")),
        ):
            transport = ASGITransport(app=app, raise_app_exceptions=False)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.post(f"/api/plan/{_VALID_UUID}/generate")
        assert resp.status_code == 500

    @pytest.mark.asyncio
    async def test_generate_corrupt_json_returns_500(self):
        """Returns 500 when session has corrupt JSON in barriers/plan."""
        row = _seed_session_row(with_plan=True)
        row["barriers"] = "not-json{{"
        with patch(_GET_SESSION_PATCH, new_callable=AsyncMock, return_value=row):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.post(f"/api/plan/{_VALID_UUID}/generate")
        assert resp.status_code == 500
        assert "Corrupt" in resp.json()["detail"]


# --- AI Client ---

class TestGetPlanCorruptData:
    @pytest.mark.asyncio
    async def test_corrupt_json_returns_500(self):
        """Returns 500 when session plan contains invalid JSON."""
        row = _seed_session_row(with_plan=False)
        row["plan"] = "not-valid-json{{"
        row["barriers"] = '["credit"]'
        with patch(_GET_SESSION_PATCH, new_callable=AsyncMock, return_value=row):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get(f"/api/plan/{_VALID_UUID}")
        assert resp.status_code == 500
        assert "Corrupt" in resp.json()["detail"]


class TestGenerateNarrative:
    @pytest.mark.asyncio
    async def test_calls_anthropic_and_parses(self):
        """generate_narrative calls Claude and returns PlanNarrative."""
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
    async def test_raises_on_empty_response(self):
        """generate_narrative raises ValueError when Claude returns empty content."""
        mock_message = MagicMock()
        mock_message.content = []
        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_message)

        with patch("app.ai.client.AsyncAnthropic", return_value=mock_client):
            with pytest.raises(ValueError, match="[Ee]mpty"):
                await generate_narrative(
                    barriers=["credit"],
                    qualifications="CNA",
                    plan_data={"barriers": []},
                )

    @pytest.mark.asyncio
    async def test_raises_on_timeout(self):
        """generate_narrative raises on API timeout."""
        from anthropic import APITimeoutError

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
        plan_data = {"barriers": [], "job_matches": [], "immediate_next_steps": []}
        result = build_fallback_narrative(
            barriers=[],
            qualifications="",
            plan_data=plan_data,
        )
        assert isinstance(result, PlanNarrative)
        assert len(result.summary) > 0


# --- GET /api/plan/{session_id}/career-center ---

def _seed_full_plan_row(session_id=_VALID_UUID_2, barriers=None, credit=None):
    """Session row with a full ReEntryPlan for career-center tests."""
    b = barriers or ["credit", "transportation"]
    plan = {
        "plan_id": "p-cc",
        "session_id": session_id,
        "barriers": [
            {"type": bt, "severity": "medium", "title": f"{bt} barrier", "actions": [f"Fix {bt}"], "resources": [], "transit_matches": []}
            for bt in b
        ],
        "job_matches": [],
        "immediate_next_steps": ["Visit Career Center"],
        "strong_matches": [],
        "possible_matches": [],
        "eligible_now": [],
        "eligible_after_repair": [],
    }
    return {
        "id": session_id,
        "created_at": "2026-03-06T12:00:00+00:00",
        "barriers": json.dumps(b),
        "credit_profile": json.dumps(credit) if credit else None,
        "qualifications": "Former CNA",
        "plan": json.dumps(plan),
        "expires_at": "2026-03-07T12:00:00+00:00",
    }


class TestCareerCenterEndpoint:
    @pytest.mark.asyncio
    async def test_returns_200_with_package(self):
        """Returns career center package for valid session with plan."""
        row = _seed_full_plan_row()
        with patch(_GET_SESSION_PATCH, new_callable=AsyncMock, return_value=row):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get(f"/api/plan/{_VALID_UUID_2}/career-center")
        assert resp.status_code == 200
        data = resp.json()
        assert "staff_summary" in data
        assert "resident_plan" in data
        assert data["resident_plan"]["career_center"]["name"] == "Montgomery Career Center"

    @pytest.mark.asyncio
    async def test_404_session_not_found(self):
        """Returns 404 when session does not exist."""
        with patch(_GET_SESSION_PATCH, new_callable=AsyncMock, return_value=None):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get(f"/api/plan/{_MISSING_UUID}/career-center")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_404_no_plan(self):
        """Returns 404 when session has no stored plan."""
        row = _seed_full_plan_row()
        row["plan"] = None
        with patch(_GET_SESSION_PATCH, new_callable=AsyncMock, return_value=row):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get(f"/api/plan/{_VALID_UUID_2}/career-center")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_wioa_populated_from_barriers(self):
        """WIOA eligibility reflects session barriers."""
        row = _seed_full_plan_row(barriers=["credit", "childcare"])
        with patch(_GET_SESSION_PATCH, new_callable=AsyncMock, return_value=row):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get(f"/api/plan/{_VALID_UUID_2}/career-center")
        data = resp.json()
        wioa = data["staff_summary"]["wioa_eligibility"]
        assert wioa["adult_program"] is True
        assert "credit" in wioa["adult_reasons"]
        assert "childcare" in wioa["adult_reasons"]

    @pytest.mark.asyncio
    async def test_credit_pathway_when_credit_data(self):
        """Credit pathway included when credit_profile exists."""
        credit = {
            "barrier_severity": "high",
            "barrier_details": [],
            "readiness": {"score": 45, "fico_score": 580, "score_band": "fair", "factors": {}},
            "thresholds": [],
            "dispute_pathway": {"steps": [{"action": "Get report"}], "total_estimated_days": 90, "statutes_cited": [], "legal_theories": []},
            "eligibility": [],
            "disclaimer": "Info only.",
        }
        row = _seed_full_plan_row(barriers=["credit"], credit=credit)
        with patch(_GET_SESSION_PATCH, new_callable=AsyncMock, return_value=row):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get(f"/api/plan/{_VALID_UUID_2}/career-center")
        data = resp.json()
        assert data["credit_pathway"] is not None
        assert len(data["credit_pathway"]["dispute_steps"]) > 0

    @pytest.mark.asyncio
    async def test_no_credit_pathway_without_credit_data(self):
        """Credit pathway absent when no credit_profile stored."""
        row = _seed_full_plan_row(barriers=["transportation"])
        with patch(_GET_SESSION_PATCH, new_callable=AsyncMock, return_value=row):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get(f"/api/plan/{_VALID_UUID_2}/career-center")
        data = resp.json()
        assert data["credit_pathway"] is None


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
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text=raw_content)]
        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_message)

        with (
            patch("app.ai.client.AsyncAnthropic", return_value=mock_client),
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

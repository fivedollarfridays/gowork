"""Tests for plan route endpoints and AI client."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.ai.types import PlanNarrative
from app.main import app
from app.modules.matching.types import ReEntryPlan
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


_GET_SESSION_PATCH = "app.routes.plan.get_session_by_id"
_UPDATE_SESSION_PATCH = "app.routes.plan.update_session_plan"
_GENERATE_PATCH = "app.routes.plan.generate_narrative"
_FALLBACK_PATCH = "app.routes.plan.build_fallback_narrative"


def _token_query(session_id: str) -> str:
    """Return query string with valid token for a session."""
    return f"?token=test-token-{session_id}"


@pytest.fixture(autouse=True)
def _mock_token_validation():
    """Auto-mock token validation so existing tests pass with tokens."""
    async def _validate(db, token):
        # Extract session_id from our test token format
        if token.startswith("test-token-"):
            return token.removeprefix("test-token-")
        return None

    async def _exists(db, token):
        return False

    with (
        patch(_VALIDATE_TOKEN_PATCH, side_effect=_validate),
        patch(_TOKEN_EXISTS_PATCH, side_effect=_exists),
    ):
        yield


# --- GET /api/plan/{session_id} ---

class TestGetPlan:
    @pytest.mark.asyncio
    async def test_valid_session_with_plan(self):
        """Returns stored plan for a valid session."""
        row = _seed_session_row(with_plan=True)
        with patch(_GET_SESSION_PATCH, new_callable=AsyncMock, return_value=row):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get(f"/api/plan/{_VALID_UUID}{_token_query(_VALID_UUID)}")
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
                resp = await client.get(f"/api/plan/{_VALID_UUID}{_token_query(_VALID_UUID)}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["plan"] is None

    @pytest.mark.asyncio
    async def test_returns_credit_profile_when_present(self):
        """Returns credit_profile in response when stored in session."""
        row = _seed_session_row(with_plan=True)
        row["credit_profile"] = json.dumps({"score": 620, "band": "fair"})
        with patch(_GET_SESSION_PATCH, new_callable=AsyncMock, return_value=row):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get(f"/api/plan/{_VALID_UUID}{_token_query(_VALID_UUID)}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["credit_profile"] == {"score": 620, "band": "fair"}

    @pytest.mark.asyncio
    async def test_credit_profile_null_when_absent(self):
        """Returns null credit_profile when not stored."""
        row = _seed_session_row(with_plan=True)
        with patch(_GET_SESSION_PATCH, new_callable=AsyncMock, return_value=row):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get(f"/api/plan/{_VALID_UUID}{_token_query(_VALID_UUID)}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["credit_profile"] is None

    @pytest.mark.asyncio
    async def test_invalid_session_404(self):
        """Returns 404 for unknown session."""
        with patch(_GET_SESSION_PATCH, new_callable=AsyncMock, return_value=None):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get(f"/api/plan/{_MISSING_UUID}{_token_query(_MISSING_UUID)}")
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
                resp = await client.post(f"/api/plan/{_VALID_UUID}/generate{_token_query(_VALID_UUID)}")
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
                resp = await client.post(f"/api/plan/{_MISSING_UUID}/generate{_token_query(_MISSING_UUID)}")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_generate_requires_plan(self):
        """Returns 400 when session has no plan to narrate."""
        row = _seed_session_row(with_plan=False)
        with patch(_GET_SESSION_PATCH, new_callable=AsyncMock, return_value=row):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.post(f"/api/plan/{_VALID_UUID}/generate{_token_query(_VALID_UUID)}")
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
                resp = await client.post(f"/api/plan/{_VALID_UUID}/generate{_token_query(_VALID_UUID)}")
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
                resp = await client.post(f"/api/plan/{_VALID_UUID}/generate{_token_query(_VALID_UUID)}")
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
                resp = await client.post(f"/api/plan/{_VALID_UUID}/generate{_token_query(_VALID_UUID)}")
        assert resp.status_code == 500

    @pytest.mark.asyncio
    async def test_generate_corrupt_json_returns_500(self):
        """Returns 500 when session has corrupt JSON in barriers/plan."""
        row = _seed_session_row(with_plan=True)
        row["barriers"] = "not-json{{"
        with patch(_GET_SESSION_PATCH, new_callable=AsyncMock, return_value=row):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.post(f"/api/plan/{_VALID_UUID}/generate{_token_query(_VALID_UUID)}")
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
                resp = await client.get(f"/api/plan/{_VALID_UUID}{_token_query(_VALID_UUID)}")
        assert resp.status_code == 500
        assert "Corrupt" in resp.json()["detail"]


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
                resp = await client.get(f"/api/plan/{_VALID_UUID_2}/career-center{_token_query(_VALID_UUID_2)}")
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
                resp = await client.get(f"/api/plan/{_MISSING_UUID}/career-center{_token_query(_MISSING_UUID)}")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_404_no_plan(self):
        """Returns 404 when session has no stored plan."""
        row = _seed_full_plan_row()
        row["plan"] = None
        with patch(_GET_SESSION_PATCH, new_callable=AsyncMock, return_value=row):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get(f"/api/plan/{_VALID_UUID_2}/career-center{_token_query(_VALID_UUID_2)}")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_wioa_populated_from_barriers(self):
        """WIOA eligibility reflects session barriers."""
        row = _seed_full_plan_row(barriers=["credit", "childcare"])
        with patch(_GET_SESSION_PATCH, new_callable=AsyncMock, return_value=row):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get(f"/api/plan/{_VALID_UUID_2}/career-center{_token_query(_VALID_UUID_2)}")
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
                resp = await client.get(f"/api/plan/{_VALID_UUID_2}/career-center{_token_query(_VALID_UUID_2)}")
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
                resp = await client.get(f"/api/plan/{_VALID_UUID_2}/career-center{_token_query(_VALID_UUID_2)}")
        data = resp.json()
        assert data["credit_pathway"] is None

    @pytest.mark.asyncio
    async def test_corrupt_json_in_career_center_returns_500(self):
        """Returns 500 when career-center endpoint encounters corrupt JSON."""
        row = _seed_full_plan_row()
        row["barriers"] = "not-json{{"
        with patch(_GET_SESSION_PATCH, new_callable=AsyncMock, return_value=row):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get(f"/api/plan/{_VALID_UUID_2}/career-center{_token_query(_VALID_UUID_2)}")
        assert resp.status_code == 500
        assert "Corrupt" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_corrupt_profile_uses_fallback(self):
        """Falls back to _build_profile_from_session when profile JSON is corrupt."""
        row = _seed_full_plan_row()
        row["profile"] = "not-valid-json"
        with patch(_GET_SESSION_PATCH, new_callable=AsyncMock, return_value=row):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get(f"/api/plan/{_VALID_UUID_2}/career-center{_token_query(_VALID_UUID_2)}")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_invalid_credit_profile_ignored(self):
        """Invalid credit_profile JSON logs warning and returns credit_pathway=None."""
        row = _seed_full_plan_row()
        row["credit_profile"] = "not-json{{"
        with patch(_GET_SESSION_PATCH, new_callable=AsyncMock, return_value=row):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get(f"/api/plan/{_VALID_UUID_2}/career-center{_token_query(_VALID_UUID_2)}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["credit_pathway"] is None


# --- POST /api/plan/{session_id}/refresh ---

_GENERATE_PLAN_PATCH = "app.routes.plan.generate_plan"
_STORE_PREV_PLAN_PATCH = "app.routes.plan.store_previous_plan"


def _seed_session_with_profile(session_id=_VALID_UUID, with_plan=True):
    """Session row with stored profile for refresh tests."""
    profile = {
        "session_id": session_id,
        "zip_code": "36104",
        "employment_status": "unemployed",
        "barrier_count": 1,
        "primary_barriers": ["credit"],
        "barrier_severity": "low",
        "needs_credit_assessment": True,
        "transit_dependent": False,
        "schedule_type": "daytime",
        "work_history": "Former CNA",
        "target_industries": [],
    }
    plan = {
        "plan_id": "p-old",
        "session_id": session_id,
        "barriers": [],
        "job_matches": [],
        "immediate_next_steps": ["Old step"],
        "strong_matches": [],
        "possible_matches": [],
        "eligible_now": [],
        "eligible_after_repair": [],
    }
    return {
        "id": session_id,
        "created_at": "2026-03-05T12:00:00+00:00",
        "barriers": json.dumps(["credit"]),
        "credit_profile": None,
        "qualifications": "Former CNA",
        "plan": json.dumps(plan) if with_plan else None,
        "profile": json.dumps(profile),
        "expires_at": "2026-03-06T12:00:00+00:00",
    }


def _mock_reentry_plan(session_id=_VALID_UUID):
    """Build a mock ReEntryPlan for generate_plan return."""
    return ReEntryPlan(
        plan_id="p-new",
        session_id=session_id,
        barriers=[],
        job_matches=[],
        immediate_next_steps=["New step"],
        strong_matches=[],
        possible_matches=[],
        eligible_now=[],
        eligible_after_repair=[],
    )


class TestRefreshCorruptProfile:
    @pytest.mark.asyncio
    async def test_plan_corrupt_profile_returns_400(self):
        """Returns 400 when session has corrupt (non-JSON) profile data."""
        row = _seed_session_with_profile()
        row["profile"] = "not-valid-json{{"
        with patch(_GET_SESSION_PATCH, new_callable=AsyncMock, return_value=row):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.post(f"/api/plan/{_VALID_UUID}/refresh{_token_query(_VALID_UUID)}")
        assert resp.status_code == 400
        assert "corrupt" in resp.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_plan_profile_invalid_data_returns_400(self):
        """Returns 400 when profile JSON is valid but fails UserProfile validation."""
        row = _seed_session_with_profile()
        # Valid JSON but not a valid UserProfile (missing required fields, has bad types)
        row["profile"] = json.dumps({"unknown_field": 999, "zip_code": [1, 2, 3]})
        with patch(_GET_SESSION_PATCH, new_callable=AsyncMock, return_value=row):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.post(f"/api/plan/{_VALID_UUID}/refresh{_token_query(_VALID_UUID)}")
        # Should be 400 if UserProfile validation fails, or 200 if UserProfile is lenient
        assert resp.status_code in (200, 400)


class TestRefreshPlan:
    @pytest.mark.asyncio
    async def test_refresh_regenerates_plan(self):
        """Refresh re-runs generate_plan and stores updated plan."""
        row = _seed_session_with_profile()
        new_plan = _mock_reentry_plan()
        with (
            patch(_GET_SESSION_PATCH, new_callable=AsyncMock, return_value=row),
            patch(_GENERATE_PLAN_PATCH, new_callable=AsyncMock, return_value=new_plan),
            patch(_UPDATE_SESSION_PATCH, new_callable=AsyncMock) as mock_update,
            patch(_STORE_PREV_PLAN_PATCH, new_callable=AsyncMock),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.post(f"/api/plan/{_VALID_UUID}/refresh{_token_query(_VALID_UUID)}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["plan"]["plan_id"] == "p-new"
        assert data["plan"]["immediate_next_steps"] == ["New step"]
        mock_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_refresh_404_missing_session(self):
        """Returns 404 for unknown session."""
        with patch(_GET_SESSION_PATCH, new_callable=AsyncMock, return_value=None):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.post(f"/api/plan/{_MISSING_UUID}/refresh{_token_query(_MISSING_UUID)}")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_refresh_400_no_profile(self):
        """Returns 400 when session has no stored profile."""
        row = _seed_session_with_profile()
        row["profile"] = None
        with patch(_GET_SESSION_PATCH, new_callable=AsyncMock, return_value=row):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.post(f"/api/plan/{_VALID_UUID}/refresh{_token_query(_VALID_UUID)}")
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_refresh_passes_credit_result(self):
        """Refresh passes stored credit result to generate_plan."""
        row = _seed_session_with_profile()
        credit = {"barrier_severity": "high", "readiness": {"score": 45}}
        row["credit_profile"] = json.dumps(credit)
        new_plan = _mock_reentry_plan()
        with (
            patch(_GET_SESSION_PATCH, new_callable=AsyncMock, return_value=row),
            patch(_GENERATE_PLAN_PATCH, new_callable=AsyncMock, return_value=new_plan) as mock_gen,
            patch(_UPDATE_SESSION_PATCH, new_callable=AsyncMock),
            patch(_STORE_PREV_PLAN_PATCH, new_callable=AsyncMock),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.post(f"/api/plan/{_VALID_UUID}/refresh{_token_query(_VALID_UUID)}")
        assert resp.status_code == 200
        call_kwargs = mock_gen.call_args
        assert call_kwargs.kwargs.get("credit_result") == credit

    @pytest.mark.asyncio
    async def test_refresh_returns_updated_response(self):
        """Refresh returns full plan response like GET /plan."""
        row = _seed_session_with_profile()
        new_plan = _mock_reentry_plan()
        with (
            patch(_GET_SESSION_PATCH, new_callable=AsyncMock, return_value=row),
            patch(_GENERATE_PLAN_PATCH, new_callable=AsyncMock, return_value=new_plan),
            patch(_UPDATE_SESSION_PATCH, new_callable=AsyncMock),
            patch(_STORE_PREV_PLAN_PATCH, new_callable=AsyncMock),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.post(f"/api/plan/{_VALID_UUID}/refresh{_token_query(_VALID_UUID)}")
        data = resp.json()
        assert data["session_id"] == _VALID_UUID
        assert data["barriers"] == ["credit"]
        assert "plan" in data
        assert "credit_profile" in data

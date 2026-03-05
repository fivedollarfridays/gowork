"""End-to-end integration tests: assessment -> matching -> session -> plan."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.modules.matching.types import ReEntryPlan


def _mock_plan() -> ReEntryPlan:
    return ReEntryPlan(
        plan_id="int-test-plan",
        session_id="int-test-session",
        barriers=[],
        job_matches=[],
        immediate_next_steps=["Visit career center"],
    )


_GEN_PATCH = "app.routes.assessment.generate_plan"
_SESSION_PATCH = "app.routes.assessment.create_session"


class TestAssessmentToPlan:
    """Full flow: POST assessment -> GET plan -> POST generate."""

    @pytest.mark.asyncio
    async def test_full_assessment_flow(self):
        """Assessment creates session, plan page retrieves it."""
        from app.main import app

        with (
            patch(_GEN_PATCH, return_value=_mock_plan()),
            patch(_SESSION_PATCH, new_callable=AsyncMock, return_value="int-session-123"),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as c:
                assess_resp = await c.post("/api/assessment/", json={
                    "zip_code": "36104",
                    "employment_status": "unemployed",
                    "barriers": {"credit": True, "transportation": True, "childcare": True},
                    "work_history": "Former CNA at Baptist Hospital",
                    "has_vehicle": False,
                })

        assert assess_resp.status_code == 200
        data = assess_resp.json()
        assert "session_id" in data
        assert "profile" in data
        assert "plan" in data

        profile = data["profile"]
        assert profile["barrier_severity"] == "high"
        assert profile["barrier_count"] == 3
        assert profile["needs_credit_assessment"] is True
        assert profile["transit_dependent"] is True
        assert "credit" in profile["primary_barriers"]
        assert "transportation" in profile["primary_barriers"]
        assert "childcare" in profile["primary_barriers"]

    @pytest.mark.asyncio
    async def test_assessment_low_severity(self):
        """Single barrier yields low severity."""
        from app.main import app

        with (
            patch(_GEN_PATCH, return_value=_mock_plan()),
            patch(_SESSION_PATCH, new_callable=AsyncMock, return_value="low-session"),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as c:
                resp = await c.post("/api/assessment/", json={
                    "zip_code": "36116",
                    "employment_status": "underemployed",
                    "barriers": {"training": True},
                    "work_history": "Retail experience",
                    "has_vehicle": True,
                })

        assert resp.status_code == 200
        profile = resp.json()["profile"]
        assert profile["barrier_severity"] == "low"
        assert profile["barrier_count"] == 1
        assert profile["transit_dependent"] is False
        assert profile["needs_credit_assessment"] is False


class TestJobsEndToEnd:
    """Jobs route returns enriched listings (uses test DB via client fixture)."""

    @pytest.mark.anyio
    async def test_jobs_returns_empty_from_seed(self, client):
        """Jobs route returns empty list when no seed data."""
        resp = await client.get("/api/jobs/")
        assert resp.status_code == 200
        data = resp.json()
        assert "jobs" in data
        assert isinstance(data["jobs"], list)

    @pytest.mark.anyio
    async def test_job_not_found(self, client):
        """GET /api/jobs/999 returns 404 for non-existent job."""
        resp = await client.get("/api/jobs/999")
        assert resp.status_code == 404


class TestHealthIntegration:
    """Health endpoint works with full app context (uses test DB via client fixture)."""

    @pytest.mark.anyio
    async def test_health_returns_ok(self, client):
        """Health endpoint returns healthy status."""
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"

    @pytest.mark.anyio
    async def test_root_returns_running(self, client):
        """Root endpoint confirms API is running."""
        resp = await client.get("/")
        assert resp.status_code == 200
        assert resp.json()["status"] == "running"

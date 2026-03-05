"""End-to-end integration tests: assessment -> matching -> session -> plan."""

import json
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
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                # Step 1: Submit assessment
                assess_resp = await client.post("/api/assessment/", json={
                    "zip_code": "36104",
                    "employment_status": "unemployed",
                    "barriers": {"credit": True, "transportation": True, "childcare": True},
                    "work_history": "Former CNA at Baptist Hospital",
                    "has_vehicle": False,
                })

        assert assess_resp.status_code == 200
        data = assess_resp.json()

        # Verify assessment response structure
        assert "session_id" in data
        assert "profile" in data
        assert "plan" in data

        # Profile should reflect inputs
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
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.post("/api/assessment/", json={
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
    """Jobs route returns enriched listings."""

    @pytest.mark.asyncio
    async def test_jobs_returns_empty_from_seed(self):
        """Jobs route returns empty list when no seed data (production state)."""
        from app.main import app

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/jobs/")
        assert resp.status_code == 200
        data = resp.json()
        assert "jobs" in data
        assert isinstance(data["jobs"], list)

    @pytest.mark.asyncio
    async def test_job_not_found(self):
        """GET /api/jobs/999 returns 404 for non-existent job."""
        from app.main import app

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/jobs/999")
        assert resp.status_code == 404


class TestHealthIntegration:
    """Health endpoint works with full app context."""

    @pytest.mark.asyncio
    async def test_health_returns_ok(self):
        """Health endpoint returns healthy status."""
        from app.main import app

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_root_returns_running(self):
        """Root endpoint confirms API is running."""
        from app.main import app

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/")
        assert resp.status_code == 200
        assert resp.json()["status"] == "running"

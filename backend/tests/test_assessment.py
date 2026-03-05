"""Tests for assessment endpoint and helper functions."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.modules.matching.types import (
    BarrierSeverity,
    BarrierType,
    ReEntryPlan,
)
from app.routes.assessment import determine_severity, extract_primary_barriers


def _mock_plan() -> ReEntryPlan:
    return ReEntryPlan(
        plan_id="test-plan-id",
        session_id="test-session",
        barriers=[],
        job_matches=[],
        immediate_next_steps=["Visit a career center"],
    )


class TestDetermineSeverity:
    def test_three_or_more_barriers_is_high(self):
        assert determine_severity(3) == BarrierSeverity.HIGH
        assert determine_severity(5) == BarrierSeverity.HIGH

    def test_two_barriers_is_medium(self):
        assert determine_severity(2) == BarrierSeverity.MEDIUM

    def test_one_barrier_is_low(self):
        assert determine_severity(1) == BarrierSeverity.LOW

    def test_zero_barriers_is_low(self):
        assert determine_severity(0) == BarrierSeverity.LOW


class TestExtractPrimaryBarriers:
    def test_returns_true_barriers(self):
        barriers = {
            BarrierType.CREDIT: True,
            BarrierType.TRANSPORTATION: False,
            BarrierType.CHILDCARE: True,
        }
        result = extract_primary_barriers(barriers)
        assert BarrierType.CREDIT in result
        assert BarrierType.CHILDCARE in result
        assert BarrierType.TRANSPORTATION not in result

    def test_empty_dict_returns_empty(self):
        assert extract_primary_barriers({}) == []

    def test_all_false_returns_empty(self):
        barriers = {
            BarrierType.CREDIT: False,
            BarrierType.HOUSING: False,
        }
        assert extract_primary_barriers(barriers) == []


_GEN_PATCH = "app.routes.assessment.generate_plan"
_SESSION_PATCH = "app.routes.assessment.create_session"


class TestAssessmentEndpoint:
    @pytest.mark.asyncio
    async def test_valid_assessment_returns_profile(self):
        """Valid request returns session_id and profile."""
        from app.main import app

        with (
            patch(_GEN_PATCH, return_value=_mock_plan()),
            patch(_SESSION_PATCH, return_value="test-uuid"),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.post("/api/assessment/", json={
                    "zip_code": "36104",
                    "employment_status": "unemployed",
                    "barriers": {"credit": True, "transportation": True},
                    "work_history": "Former CNA at Baptist Hospital",
                })
        assert resp.status_code == 200
        data = resp.json()
        assert "session_id" in data
        assert "profile" in data
        assert "plan" in data

    @pytest.mark.asyncio
    async def test_invalid_zip_rejected(self):
        """Non-Montgomery zip should be rejected."""
        from app.main import app

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/api/assessment/", json={
                "zip_code": "90210",
                "employment_status": "unemployed",
                "barriers": {"credit": True},
                "work_history": "Some work history",
            })
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_barrier_count_determines_severity(self):
        """Severity should match barrier count."""
        from app.main import app

        with (
            patch(_GEN_PATCH, return_value=_mock_plan()),
            patch(_SESSION_PATCH, return_value="test-uuid"),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.post("/api/assessment/", json={
                    "zip_code": "36104",
                    "employment_status": "unemployed",
                    "barriers": {
                        "credit": True,
                        "transportation": True,
                        "childcare": True,
                    },
                    "work_history": "Some work",
                })
        data = resp.json()
        assert data["profile"]["barrier_severity"] == "high"

    @pytest.mark.asyncio
    async def test_credit_barrier_sets_needs_assessment(self):
        """Credit barrier should set needs_credit_assessment flag."""
        from app.main import app

        with (
            patch(_GEN_PATCH, return_value=_mock_plan()),
            patch(_SESSION_PATCH, return_value="test-uuid"),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.post("/api/assessment/", json={
                    "zip_code": "36104",
                    "employment_status": "unemployed",
                    "barriers": {"credit": True},
                    "work_history": "Some work",
                })
        data = resp.json()
        assert data["profile"]["needs_credit_assessment"] is True

    @pytest.mark.asyncio
    async def test_no_vehicle_sets_transit_dependent(self):
        """No vehicle + transportation barrier should set transit_dependent."""
        from app.main import app

        with (
            patch(_GEN_PATCH, return_value=_mock_plan()),
            patch(_SESSION_PATCH, return_value="test-uuid"),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.post("/api/assessment/", json={
                    "zip_code": "36104",
                    "employment_status": "unemployed",
                    "barriers": {"transportation": True},
                    "work_history": "Some work",
                    "has_vehicle": False,
                })
        data = resp.json()
        assert data["profile"]["transit_dependent"] is True

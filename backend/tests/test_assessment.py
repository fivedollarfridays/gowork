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


class TestRateLimiter:
    def test_allows_requests_under_limit(self):
        from app.routes.assessment import _rate_limiter
        _rate_limiter.clear()
        for _ in range(10):
            assert _rate_limiter.check("1.2.3.4") is True

    def test_blocks_requests_over_limit(self):
        from app.routes.assessment import _rate_limiter
        _rate_limiter.clear()
        for _ in range(10):
            _rate_limiter.check("5.6.7.8")
        assert _rate_limiter.check("5.6.7.8") is False

    def test_different_ips_independent(self):
        from app.routes.assessment import _rate_limiter
        _rate_limiter.clear()
        for _ in range(10):
            _rate_limiter.check("10.0.0.1")
        assert _rate_limiter.check("10.0.0.1") is False
        assert _rate_limiter.check("10.0.0.2") is True


_GEN_PATCH = "app.routes.assessment.generate_plan"
_SESSION_PATCH = "app.routes.assessment.create_session"
_UPDATE_PLAN_PATCH = "app.routes.assessment.update_session_plan"
_FEEDBACK_TOKEN_PATCH = "app.routes.assessment.create_feedback_token"


class TestAssessmentEndpoint:
    @pytest.fixture(autouse=True)
    def _clear_rate_limiter(self):
        from app.routes.assessment import _rate_limiter
        _rate_limiter.clear()

    @pytest.mark.asyncio
    async def test_valid_assessment_returns_profile(self):
        """Valid request returns session_id and profile."""
        from app.main import app

        with (
            patch(_GEN_PATCH, return_value=_mock_plan()),
            patch(_SESSION_PATCH, return_value="test-uuid"),
            patch(_UPDATE_PLAN_PATCH, new_callable=AsyncMock),
            patch(_FEEDBACK_TOKEN_PATCH, new_callable=AsyncMock, return_value="test-token"),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.post("/api/assessment/", json={
                    "zip_code": "36104",
                    "employment_status": "unemployed",
                    "barriers": {"credit": True, "transportation": True},
                    "work_history": "Former CNA at Baptist Hospital",
                })
        assert resp.status_code == 201
        data = resp.json()
        assert "session_id" in data
        assert "profile" in data
        assert "plan" in data
        assert data["feedback_token"] == "test-token"

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
            patch(_UPDATE_PLAN_PATCH, new_callable=AsyncMock),
            patch(_FEEDBACK_TOKEN_PATCH, new_callable=AsyncMock, return_value="test-token"),
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
            patch(_UPDATE_PLAN_PATCH, new_callable=AsyncMock),
            patch(_FEEDBACK_TOKEN_PATCH, new_callable=AsyncMock, return_value="test-token"),
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
            patch(_UPDATE_PLAN_PATCH, new_callable=AsyncMock),
            patch(_FEEDBACK_TOKEN_PATCH, new_callable=AsyncMock, return_value="test-token"),
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

    @pytest.mark.asyncio
    async def test_db_failure_returns_500(self):
        """Returns 500 when create_session raises."""
        from app.main import app

        with (
            patch(_SESSION_PATCH, new_callable=AsyncMock, side_effect=RuntimeError("DB down")),
        ):
            transport = ASGITransport(app=app, raise_app_exceptions=False)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.post("/api/assessment/", json={
                    "zip_code": "36104",
                    "employment_status": "unemployed",
                    "barriers": {"credit": True},
                    "work_history": "Some work",
                })
        assert resp.status_code == 500

    @pytest.mark.asyncio
    async def test_engine_failure_returns_500(self):
        """Returns 500 when generate_plan raises."""
        from app.main import app

        with (
            patch(_SESSION_PATCH, return_value="test-uuid"),
            patch(_GEN_PATCH, side_effect=RuntimeError("Engine crash")),
        ):
            transport = ASGITransport(app=app, raise_app_exceptions=False)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.post("/api/assessment/", json={
                    "zip_code": "36104",
                    "employment_status": "unemployed",
                    "barriers": {"credit": True},
                    "work_history": "Some work",
                })
        assert resp.status_code == 500

    @pytest.mark.asyncio
    async def test_rate_limit_returns_429(self):
        """Returns 429 when rate limit exceeded."""
        from app.main import app
        from app.routes.assessment import _rate_limiter

        _rate_limiter.clear()

        with (
            patch(_GEN_PATCH, return_value=_mock_plan()),
            patch(_SESSION_PATCH, return_value="test-uuid"),
            patch(_UPDATE_PLAN_PATCH, new_callable=AsyncMock),
            patch(_FEEDBACK_TOKEN_PATCH, new_callable=AsyncMock, return_value="test-token"),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                payload = {
                    "zip_code": "36104",
                    "employment_status": "unemployed",
                    "barriers": {"credit": True},
                    "work_history": "Some work",
                }
                for _ in range(10):
                    resp = await client.post("/api/assessment/", json=payload)
                    assert resp.status_code == 201
                # 11th should be rate limited
                resp = await client.post("/api/assessment/", json=payload)
                assert resp.status_code == 429

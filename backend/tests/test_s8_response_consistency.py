"""S8 Polish: response format consistency tests (Donatello).

Ensures every endpoint returns consistent, well-formed JSON responses
with proper HTTP status codes for both success and error cases.
"""

import json
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text

from app.core.database import get_async_session_factory
from app.routes.share import _rate_limiter


@pytest.fixture(autouse=True)
def _clear_rate_limiters():
    _rate_limiter.clear()
    yield
    _rate_limiter.clear()


async def _create_full_session(
    test_engine,
    session_id: str,
    *,
    auth_token: str,
    barriers: list[str] | None = None,
    plan: dict | None = None,
) -> None:
    """Insert a complete session with all fields."""
    factory = get_async_session_factory()
    async with factory() as db:
        now = datetime.now(timezone.utc)
        expires = (now + timedelta(days=30)).isoformat()
        plan_json = json.dumps(plan or {
            "plan_id": "test", "session_id": session_id,
            "barriers": [], "immediate_next_steps": ["Visit career center"],
        })
        await db.execute(
            text(
                "INSERT INTO sessions (id, created_at, barriers, plan, expires_at) "
                "VALUES (:id, :ts, :b, :p, :exp)"
            ),
            {
                "id": session_id,
                "ts": now.isoformat(),
                "b": json.dumps(barriers or ["credit"]),
                "p": plan_json,
                "exp": expires,
            },
        )
        await db.execute(
            text(
                "INSERT INTO feedback_tokens (token, session_id, created_at, expires_at) "
                "VALUES (:tok, :sid, :ts, :exp)"
            ),
            {"tok": auth_token, "sid": session_id, "ts": now.isoformat(), "exp": expires},
        )
        await db.commit()


# ---------------------------------------------------------------------------
# Error response format: all errors should return {"detail": "..."}
# ---------------------------------------------------------------------------


class TestErrorResponseFormat:
    """All error responses should have a consistent {"detail": "..."} shape."""

    @pytest.mark.anyio
    async def test_401_has_detail(self, client, test_engine):
        """Unauthorized responses include detail field."""
        resp = await client.get(
            "/api/plan/00000000-0000-4000-8000-aaa000000001/sequence?token=bad"
        )
        assert resp.status_code == 401
        data = resp.json()
        assert "detail" in data

    @pytest.mark.anyio
    async def test_422_has_detail(self, client, test_engine):
        """Validation errors include detail field."""
        resp = await client.post(
            "/api/pathway?token=any",
            json={"session_id": "not-a-uuid", "current_wage": 10.0},
        )
        assert resp.status_code == 422
        data = resp.json()
        assert "detail" in data

    @pytest.mark.anyio
    async def test_404_share_has_detail(self, client, test_engine):
        """Missing share token returns 404 with detail."""
        resp = await client.get("/api/plan/shared/nonexistent-token")
        assert resp.status_code == 404
        data = resp.json()
        assert "detail" in data

    @pytest.mark.anyio
    async def test_400_no_plan_has_detail(self, client, test_engine):
        """Sharing session without plan returns 400 with detail."""
        sid = "00000000-0000-4000-8000-ae5000000001"
        factory = get_async_session_factory()
        async with factory() as db:
            now = datetime.now(timezone.utc)
            expires = (now + timedelta(days=30)).isoformat()
            await db.execute(
                text(
                    "INSERT INTO sessions (id, created_at, barriers, plan, expires_at) "
                    "VALUES (:id, :ts, :b, NULL, :exp)"
                ),
                {"id": sid, "ts": now.isoformat(), "b": "[]", "exp": expires},
            )
            await db.execute(
                text(
                    "INSERT INTO feedback_tokens (token, session_id, created_at, expires_at) "
                    "VALUES (:tok, :sid, :ts, :exp)"
                ),
                {"tok": "resp-tok-1", "sid": sid, "ts": now.isoformat(), "exp": expires},
            )
            await db.commit()

        resp = await client.post(f"/api/plan/{sid}/share?token=resp-tok-1")
        assert resp.status_code == 400
        data = resp.json()
        assert "detail" in data


# ---------------------------------------------------------------------------
# Success response format consistency
# ---------------------------------------------------------------------------


class TestSuccessResponseFormat:
    """Verify success responses have consistent shapes."""

    @pytest.mark.anyio
    async def test_dashboard_stats_format(self, client, test_engine):
        """Dashboard stats returns expected keys with correct types."""
        resp = await client.get("/api/dashboard/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data["total_assessments"], int)
        assert isinstance(data["common_barriers"], list)
        assert isinstance(data["total_barrier_instances"], int)

    @pytest.mark.anyio
    async def test_outcomes_aggregate_format(self, client, test_engine):
        """Outcomes aggregate returns expected keys."""
        resp = await client.get("/api/outcomes/aggregate")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data["assessment_count"], int)
        assert isinstance(data["top_barriers"], list)

    @pytest.mark.anyio
    async def test_pathway_response_format(self, client, test_engine):
        """Pathway response has pathways list with expected structure."""
        sid = "00000000-0000-4000-8000-ae5000000002"
        await _create_full_session(
            test_engine, sid,
            auth_token="resp-tok-2",
            barriers=["credit", "transportation"],
        )
        resp = await client.post(
            f"/api/pathway?token=resp-tok-2",
            json={"session_id": sid, "current_wage": 10.0},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "pathways" in data
        assert isinstance(data["pathways"], list)
        if data["pathways"]:
            pw = data["pathways"][0]
            assert "pathway_id" in pw
            assert "name" in pw
            assert "steps" in pw
            assert "viability_score" in pw

    @pytest.mark.anyio
    async def test_sequence_response_format(self, client, test_engine):
        """Sequence response has steps list with expected fields."""
        sid = "00000000-0000-4000-8000-ae5000000003"
        await _create_full_session(
            test_engine, sid,
            auth_token="resp-tok-3",
            barriers=["credit", "housing"],
        )
        resp = await client.get(f"/api/plan/{sid}/sequence?token=resp-tok-3")
        assert resp.status_code == 200
        data = resp.json()
        assert "steps" in data
        assert "total_barriers" in data
        assert "has_cycles" in data
        assert "estimated_total_weeks" in data
        for step in data["steps"]:
            assert "barrier_id" in step
            assert "barrier_name" in step
            assert "order" in step
            assert "unlocks" in step
            assert "category" in step
            assert "estimated_weeks" in step

    @pytest.mark.anyio
    async def test_simulate_response_format(self, client, test_engine):
        """Simulate response has all documented fields."""
        sid = "00000000-0000-4000-8000-ae5000000004"
        await _create_full_session(
            test_engine, sid,
            auth_token="resp-tok-4",
            barriers=["credit"],
        )
        resp = await client.post(
            f"/api/simulate?token=resp-tok-4",
            json={"session_id": sid, "resolved_barriers": ["credit"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        expected_keys = {
            "barriers_resolved", "barriers_remaining", "unlocked_barriers",
            "jobs_unlocked_estimate", "benefits_unlocked", "sequence_after",
            "confidence",
        }
        assert expected_keys.issubset(data.keys())
        assert isinstance(data["barriers_resolved"], list)
        assert isinstance(data["barriers_remaining"], list)
        assert isinstance(data["jobs_unlocked_estimate"], int)
        assert data["confidence"] in ("low", "medium", "high")

    @pytest.mark.anyio
    async def test_share_create_response_format(self, client, test_engine):
        """Share creation returns share_token and url."""
        sid = "00000000-0000-4000-8000-ae5000000005"
        await _create_full_session(
            test_engine, sid,
            auth_token="resp-tok-5",
        )
        resp = await client.post(f"/api/plan/{sid}/share?token=resp-tok-5")
        assert resp.status_code == 200
        data = resp.json()
        assert "share_token" in data
        assert "url" in data
        assert isinstance(data["share_token"], str)
        assert len(data["share_token"]) > 0

    @pytest.mark.anyio
    async def test_shared_plan_response_format(self, client, test_engine):
        """Shared plan retrieval has all expected fields."""
        sid = "00000000-0000-4000-8000-ae5000000006"
        await _create_full_session(
            test_engine, sid,
            auth_token="resp-tok-6",
        )
        r1 = await client.post(f"/api/plan/{sid}/share?token=resp-tok-6")
        share_tok = r1.json()["share_token"]

        r2 = await client.get(f"/api/plan/shared/{share_tok}")
        assert r2.status_code == 200
        data = r2.json()
        expected_keys = {
            "session_id", "created_at", "barriers",
            "next_steps", "career_center_name", "career_center_phone",
        }
        assert expected_keys.issubset(data.keys())

    @pytest.mark.anyio
    async def test_intelligence_response_format(self, client, test_engine):
        """Intelligence response has all documented fields."""
        resp = await client.get("/api/intelligence/barriers")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data["barriers"], list)
        assert isinstance(data["calibrated_weeks"], dict)
        assert isinstance(data["default_weeks"], dict)
        assert isinstance(data["total_feedback_count"], int)

    @pytest.mark.anyio
    async def test_city_endpoint_format(self, client, test_engine):
        """City endpoint returns expected structure."""
        resp = await client.get("/api/city")
        assert resp.status_code == 200
        data = resp.json()
        assert "name" in data
        assert "state" in data
        assert "location" in data
        assert "zip_ranges" in data
        assert isinstance(data["name"], str)
        assert isinstance(data["zip_ranges"], list)


# ---------------------------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------------------------


class TestHealthEndpoint:
    """Verify health endpoint returns expected format."""

    @pytest.mark.anyio
    async def test_health_returns_200(self, client, test_engine):
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("status") == "ok" or "status" in data

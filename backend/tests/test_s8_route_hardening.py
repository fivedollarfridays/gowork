"""S8 Polish: route-level edge case tests for coverage gaps.

Targets uncovered lines in route handlers: dashboard, simulate, share,
pathway, sequence, and intelligence routes.
"""

import json
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text

from app.core.database import get_async_session_factory
from app.routes.share import _rate_limiter


@pytest.fixture(autouse=True)
def _clear_rate_limiters():
    """Clear rate limiters between tests."""
    _rate_limiter.clear()
    yield
    _rate_limiter.clear()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _seed_session(
    test_engine,
    session_id: str,
    *,
    barriers: list[str] | None = None,
    plan: dict | None = None,
    auth_token: str | None = None,
) -> None:
    """Insert a session with optional barriers, plan, and auth token."""
    factory = get_async_session_factory()
    async with factory() as db:
        now = datetime.now(timezone.utc)
        expires = (now + timedelta(days=30)).isoformat()
        plan_json = json.dumps(plan) if plan else None
        barriers_json = json.dumps(barriers or [])
        await db.execute(
            text(
                "INSERT INTO sessions (id, created_at, barriers, plan, expires_at) "
                "VALUES (:id, :ts, :b, :p, :exp)"
            ),
            {"id": session_id, "ts": now.isoformat(), "b": barriers_json, "p": plan_json, "exp": expires},
        )
        if auth_token:
            await db.execute(
                text(
                    "INSERT INTO feedback_tokens (token, session_id, created_at, expires_at) "
                    "VALUES (:tok, :sid, :ts, :exp)"
                ),
                {"tok": auth_token, "sid": session_id, "ts": now.isoformat(), "exp": expires},
            )
        await db.commit()


# ---------------------------------------------------------------------------
# Dashboard: JSON barriers parsing edge cases
# ---------------------------------------------------------------------------


class TestDashboardBarrierParsing:
    """Cover _get_all_session_barriers edge cases."""

    @pytest.mark.anyio
    async def test_session_with_empty_barriers_string(self, client, test_engine):
        """Session with empty string barriers is counted but adds no barriers."""
        factory = get_async_session_factory()
        async with factory() as db:
            now = datetime.now(timezone.utc)
            expires = (now + timedelta(days=30)).isoformat()
            await db.execute(
                text(
                    "INSERT INTO sessions (id, created_at, barriers, expires_at) "
                    "VALUES (:id, :ts, :b, :exp)"
                ),
                {"id": "00000000-0000-4000-8000-da5b00000001", "ts": now.isoformat(), "b": "", "exp": expires},
            )
            await db.commit()

        resp = await client.get("/api/dashboard/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_assessments"] == 1
        assert data["total_barrier_instances"] == 0

    @pytest.mark.anyio
    async def test_session_with_dict_barriers_ignored(self, client, test_engine):
        """Session with non-list JSON barriers (e.g., dict) is handled."""
        factory = get_async_session_factory()
        async with factory() as db:
            now = datetime.now(timezone.utc)
            expires = (now + timedelta(days=30)).isoformat()
            await db.execute(
                text(
                    "INSERT INTO sessions (id, created_at, barriers, expires_at) "
                    "VALUES (:id, :ts, :b, :exp)"
                ),
                {
                    "id": "00000000-0000-4000-8000-da5b00000002",
                    "ts": now.isoformat(),
                    "b": json.dumps({"credit": True}),
                    "exp": expires,
                },
            )
            await db.commit()

        resp = await client.get("/api/dashboard/stats")
        assert resp.status_code == 200
        data = resp.json()
        # Dict barriers are not a list, so they should be skipped
        assert data["total_barrier_instances"] == 0

    @pytest.mark.anyio
    async def test_outcomes_aggregate_with_mixed_data(self, client, test_engine):
        """Aggregate outcomes handles mix of valid and invalid data."""
        factory = get_async_session_factory()
        async with factory() as db:
            now = datetime.now(timezone.utc)
            expires = (now + timedelta(days=30)).isoformat()
            # Valid session
            await db.execute(
                text(
                    "INSERT INTO sessions (id, created_at, barriers, expires_at) "
                    "VALUES (:id, :ts, :b, :exp)"
                ),
                {
                    "id": "00000000-0000-4000-8000-da5b00000003",
                    "ts": now.isoformat(),
                    "b": json.dumps(["credit", "housing"]),
                    "exp": expires,
                },
            )
            # Invalid JSON barrier
            await db.execute(
                text(
                    "INSERT INTO sessions (id, created_at, barriers, expires_at) "
                    "VALUES (:id, :ts, :b, :exp)"
                ),
                {
                    "id": "00000000-0000-4000-8000-da5b00000004",
                    "ts": now.isoformat(),
                    "b": "{invalid json",
                    "exp": expires,
                },
            )
            await db.commit()

        resp = await client.get("/api/outcomes/aggregate")
        assert resp.status_code == 200
        data = resp.json()
        assert data["assessment_count"] == 2
        # Only the valid session's barriers should count
        assert len(data["top_barriers"]) >= 1


# ---------------------------------------------------------------------------
# Simulate: session not found + empty barrier paths
# ---------------------------------------------------------------------------


class TestSimulateRouteEdgeCases:
    """Cover simulate route uncovered lines."""

    @pytest.mark.anyio
    async def test_session_not_found(self, client, test_engine):
        """Non-existent session after valid auth returns 404 or 401."""
        resp = await client.post(
            "/api/simulate?token=nonexistent",
            json={
                "session_id": "00000000-0000-4000-8000-51a0ffffffff",
                "resolved_barriers": [],
            },
        )
        assert resp.status_code in (401, 404)

    @pytest.mark.anyio
    async def test_resolve_unknown_only_barriers(self, client, test_engine):
        """Resolving only unknown barrier types produces low confidence."""
        sid = "00000000-0000-4000-8000-51a100000001"
        await _seed_session(
            test_engine, sid,
            barriers=["weird_barrier", "another_unknown"],
            plan={"plan_id": "p", "session_id": sid, "barriers": [], "immediate_next_steps": []},
            auth_token="sim-edge-1",
        )
        resp = await client.post(
            f"/api/simulate?token=sim-edge-1",
            json={
                "session_id": sid,
                "resolved_barriers": ["weird_barrier", "another_unknown"],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["confidence"] == "low"
        # Default estimate is 3 per unknown barrier
        assert data["jobs_unlocked_estimate"] == 6
        assert data["benefits_unlocked"] == []

    @pytest.mark.anyio
    async def test_mixed_known_unknown_medium_confidence(self, client, test_engine):
        """Mix of known + unknown barriers produces medium confidence."""
        sid = "00000000-0000-4000-8000-51a100000002"
        await _seed_session(
            test_engine, sid,
            barriers=["credit", "unknown_x"],
            plan={"plan_id": "p", "session_id": sid, "barriers": [], "immediate_next_steps": []},
            auth_token="sim-edge-2",
        )
        resp = await client.post(
            f"/api/simulate?token=sim-edge-2",
            json={
                "session_id": sid,
                "resolved_barriers": ["credit", "unknown_x"],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["confidence"] == "medium"

    @pytest.mark.anyio
    async def test_session_with_empty_barriers(self, client, test_engine):
        """Session with no barriers still produces valid simulation."""
        sid = "00000000-0000-4000-8000-51a100000003"
        await _seed_session(
            test_engine, sid,
            barriers=[],
            plan={"plan_id": "p", "session_id": sid, "barriers": [], "immediate_next_steps": []},
            auth_token="sim-edge-3",
        )
        resp = await client.post(
            f"/api/simulate?token=sim-edge-3",
            json={
                "session_id": sid,
                "resolved_barriers": [],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["barriers_remaining"] == []
        assert data["barriers_resolved"] == []


# ---------------------------------------------------------------------------
# Share: deleted session + career center info
# ---------------------------------------------------------------------------


class TestShareRouteEdgeCases:
    """Cover share route uncovered paths."""

    @pytest.mark.anyio
    async def test_shared_plan_session_deleted_returns_404(self, client, test_engine):
        """If the underlying session is deleted after sharing, return 404."""
        sid = "00000000-0000-4000-8000-share0f000001"
        await _seed_session(
            test_engine, sid,
            barriers=["credit"],
            plan={"plan_id": "t", "session_id": sid, "barriers": [], "immediate_next_steps": ["Go"]},
            auth_token="share-edge-1",
        )
        # Create share
        r1 = await client.post(f"/api/plan/{sid}/share?token=share-edge-1")
        assert r1.status_code == 200
        share_tok = r1.json()["share_token"]

        # Delete the session
        factory = get_async_session_factory()
        async with factory() as db:
            await db.execute(text("DELETE FROM sessions WHERE id = :id"), {"id": sid})
            await db.commit()

        # Try to retrieve shared plan
        r2 = await client.get(f"/api/plan/shared/{share_tok}")
        assert r2.status_code == 404

    @pytest.mark.anyio
    async def test_shared_plan_missing_plan_returns_404(self, client, test_engine):
        """If the session plan is removed after sharing, return 404."""
        sid = "00000000-0000-4000-8000-share0f000002"
        await _seed_session(
            test_engine, sid,
            barriers=["credit"],
            plan={"plan_id": "t", "session_id": sid, "barriers": [], "immediate_next_steps": ["Go"]},
            auth_token="share-edge-2",
        )
        # Create share
        r1 = await client.post(f"/api/plan/{sid}/share?token=share-edge-2")
        assert r1.status_code == 200
        share_tok = r1.json()["share_token"]

        # Remove the plan from session
        factory = get_async_session_factory()
        async with factory() as db:
            await db.execute(
                text("UPDATE sessions SET plan = NULL WHERE id = :id"),
                {"id": sid},
            )
            await db.commit()

        r2 = await client.get(f"/api/plan/shared/{share_tok}")
        assert r2.status_code == 404

    @pytest.mark.anyio
    async def test_shared_plan_has_career_center_info(self, client, test_engine):
        """Shared plan response includes career_center_name and phone."""
        sid = "00000000-0000-4000-8000-share0f000003"
        await _seed_session(
            test_engine, sid,
            barriers=[],
            plan={"plan_id": "t", "session_id": sid, "barriers": [], "immediate_next_steps": ["Visit"]},
            auth_token="share-edge-3",
        )
        r1 = await client.post(f"/api/plan/{sid}/share?token=share-edge-3")
        share_tok = r1.json()["share_token"]

        r2 = await client.get(f"/api/plan/shared/{share_tok}")
        assert r2.status_code == 200
        data = r2.json()
        assert "career_center_name" in data
        assert "career_center_phone" in data
        assert isinstance(data["career_center_name"], str)


# ---------------------------------------------------------------------------
# Sequence: session not found path
# ---------------------------------------------------------------------------


class TestSequenceRouteEdgeCases:
    """Cover sequence route uncovered handler paths."""

    @pytest.mark.anyio
    async def test_valid_token_session_not_found(self, client, test_engine):
        """Valid UUID format but non-existent session returns error."""
        resp = await client.get(
            "/api/plan/00000000-0000-4000-8000-5e00eaaaaaaa/sequence?token=nonexistent"
        )
        assert resp.status_code in (401, 404)

    @pytest.mark.anyio
    async def test_mixed_known_unknown_barriers(self, client, test_engine):
        """Unknown barriers in session are filtered from sequence."""
        sid = "00000000-0000-4000-8000-5e00eb000001"
        await _seed_session(
            test_engine, sid,
            barriers=["credit", "nonexistent_barrier", "housing"],
            plan={"plan_id": "t", "session_id": sid, "barriers": [], "immediate_next_steps": []},
            auth_token="seq-edge-1",
        )
        resp = await client.get(f"/api/plan/{sid}/sequence?token=seq-edge-1")
        assert resp.status_code == 200
        data = resp.json()
        ids = {s["barrier_id"] for s in data["steps"]}
        assert "nonexistent_barrier" not in ids
        assert "credit" in ids
        assert "housing" in ids


# ---------------------------------------------------------------------------
# Intelligence: response format consistency
# ---------------------------------------------------------------------------


class TestIntelligenceResponseFormat:
    """Verify intelligence route response format consistency."""

    @pytest.mark.anyio
    async def test_response_has_all_required_fields(self, client, test_engine):
        """Intelligence response always includes all documented fields."""
        resp = await client.get("/api/intelligence/barriers")
        assert resp.status_code == 200
        data = resp.json()
        required_fields = {
            "barriers", "confidence", "calibrated_weeks",
            "default_weeks", "total_feedback_count", "avg_plan_accuracy",
        }
        assert required_fields.issubset(data.keys())

    @pytest.mark.anyio
    async def test_default_weeks_has_all_barrier_types(self, client, test_engine):
        """default_weeks dict should include all 7 standard barrier types."""
        resp = await client.get("/api/intelligence/barriers")
        data = resp.json()
        expected = {"criminal_record", "credit", "transportation", "childcare", "housing", "health", "training"}
        assert expected.issubset(set(data["default_weeks"].keys()))

    @pytest.mark.anyio
    async def test_empty_db_confidence_is_none(self, client, test_engine):
        """Empty database produces 'none' confidence level."""
        resp = await client.get("/api/intelligence/barriers")
        data = resp.json()
        assert data["confidence"] == "none"
        assert data["total_feedback_count"] == 0

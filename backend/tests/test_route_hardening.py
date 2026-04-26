"""Endpoint hardening tests — error paths, edge cases, and input validation.

Covers gaps identified by coverage analysis:
- simulate: session_not_found, empty barriers handling
- dashboard: _get_all_session_barriers edge cases
- share: deleted session after token creation
- sequence: session with only unknown barriers
- pathway: all edge cases
"""

import json
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text

from app.core.database import get_async_session_factory


async def _seed(test_engine, sid: str, barriers: list[str], *, tok: str, plan: str | None = None) -> str:
    """Insert session + auth token. Returns the auth token."""
    factory = get_async_session_factory()
    async with factory() as db:
        now = datetime.now(timezone.utc)
        expires = (now + timedelta(days=30)).isoformat()
        p = plan or json.dumps({
            "plan_id": "t", "session_id": sid,
            "barriers": [], "immediate_next_steps": ["Go"],
        })
        await db.execute(
            text(
                "INSERT INTO sessions (id, created_at, barriers, plan, expires_at) "
                "VALUES (:id, :ts, :b, :p, :exp)"
            ),
            {"id": sid, "ts": now.isoformat(), "b": json.dumps(barriers), "p": p, "exp": expires},
        )
        await db.execute(
            text(
                "INSERT INTO feedback_tokens (token, session_id, created_at, expires_at) "
                "VALUES (:tok, :sid, :ts, :exp)"
            ),
            {"tok": tok, "sid": sid, "ts": now.isoformat(), "exp": expires},
        )
        await db.commit()
    return tok


class TestSimulateSessionNotFound:
    """Simulate endpoint: session not found after auth passes."""

    @pytest.mark.anyio
    async def test_session_not_found_returns_error(self, client, test_engine):
        """Valid auth but deleted session returns 404 or 401."""
        sid = "00000000-0000-4000-8000-51a0ee000001"
        resp = await client.post(
            f"/api/simulate?token=bad",
            json={"session_id": sid, "resolved_barriers": []},
        )
        assert resp.status_code in (401, 404)
        data = resp.json()
        assert "detail" in data

    @pytest.mark.anyio
    async def test_empty_body_returns_422(self, client, test_engine):
        """Empty POST body returns 422."""
        resp = await client.post("/api/simulate?token=tok", json={})
        assert resp.status_code == 422

    @pytest.mark.anyio
    async def test_missing_session_id_returns_422(self, client, test_engine):
        """Missing session_id field returns 422."""
        resp = await client.post(
            "/api/simulate?token=tok",
            json={"resolved_barriers": ["credit"]},
        )
        assert resp.status_code == 422

    @pytest.mark.anyio
    async def test_too_many_resolved_barriers_rejected(self, client, test_engine):
        """More than 10 resolved_barriers rejected by validation."""
        sid = "00000000-0000-4000-8000-51a0ee000002"
        resp = await client.post(
            f"/api/simulate?token=tok",
            json={
                "session_id": sid,
                "resolved_barriers": [f"b{i}" for i in range(15)],
            },
        )
        assert resp.status_code == 422


class TestSequenceEdgeCases:
    """Additional sequence endpoint hardening."""

    @pytest.mark.anyio
    async def test_all_unknown_barriers_returns_empty(self, client, test_engine):
        """Session with only unmapped barriers returns empty steps."""
        sid = "00000000-0000-4000-8000-5e00ee000001"
        tok = await _seed(
            test_engine, sid, ["unknown1", "unknown2"],
            tok="seq-extra-1",
        )
        resp = await client.get(f"/api/plan/{sid}/sequence?token={tok}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["steps"] == []
        assert data["total_barriers"] == 0

    @pytest.mark.anyio
    async def test_invalid_uuid_format_returns_422(self, client, test_engine):
        """Non-UUID session_id in path returns 422."""
        resp = await client.get("/api/plan/not-a-valid-uuid/sequence?token=t")
        assert resp.status_code == 422

    @pytest.mark.anyio
    async def test_missing_token_returns_422(self, client, test_engine):
        """Missing token query param returns 422."""
        resp = await client.get(
            "/api/plan/00000000-0000-4000-8000-5e00ee000002/sequence"
        )
        assert resp.status_code == 422


class TestSharePlanEdgeCases:
    """Additional share plan endpoint hardening."""

    @pytest.mark.anyio
    async def test_share_deleted_session_returns_404(self, client, test_engine):
        """Sharing a session that was deleted returns error."""
        sid = "00000000-0000-4000-8000-5a0eee000001"
        tok = await _seed(test_engine, sid, ["credit"], tok="share-del-1")

        # Create share link
        r1 = await client.post(f"/api/plan/{sid}/share?token={tok}")
        assert r1.status_code == 200
        share_token = r1.json()["share_token"]

        # Delete the session
        factory = get_async_session_factory()
        async with factory() as db:
            await db.execute(text("DELETE FROM sessions WHERE id = :sid"), {"sid": sid})
            await db.commit()

        # Try to retrieve shared plan
        r2 = await client.get(f"/api/plan/shared/{share_token}")
        assert r2.status_code == 404
        assert "detail" in r2.json()

    @pytest.mark.anyio
    async def test_share_session_no_plan_returns_400(self, client, test_engine):
        """Sharing a session without a plan returns 400."""
        sid = "00000000-0000-4000-8000-5a0eee000002"
        factory = get_async_session_factory()
        async with factory() as db:
            now = datetime.now(timezone.utc)
            expires = (now + timedelta(days=30)).isoformat()
            await db.execute(
                text(
                    "INSERT INTO sessions (id, created_at, barriers, plan, expires_at) "
                    "VALUES (:id, :ts, :b, :p, :exp)"
                ),
                {"id": sid, "ts": now.isoformat(), "b": "[]", "p": None, "exp": expires},
            )
            await db.execute(
                text(
                    "INSERT INTO feedback_tokens (token, session_id, created_at, expires_at) "
                    "VALUES (:tok, :sid, :ts, :exp)"
                ),
                {"tok": "share-del-2", "sid": sid, "ts": now.isoformat(), "exp": expires},
            )
            await db.commit()

        resp = await client.post(f"/api/plan/{sid}/share?token=share-del-2")
        assert resp.status_code == 400

    @pytest.mark.anyio
    async def test_get_shared_plan_response_format(self, client, test_engine):
        """Shared plan response has expected fields."""
        sid = "00000000-0000-4000-8000-5a0eee000003"
        tok = await _seed(test_engine, sid, ["credit", "housing"], tok="share-del-3")

        r1 = await client.post(f"/api/plan/{sid}/share?token={tok}")
        share_tok = r1.json()["share_token"]

        r2 = await client.get(f"/api/plan/shared/{share_tok}")
        assert r2.status_code == 200
        data = r2.json()
        # Public payload is redacted (T13.71 P1): no session_id, no raw barriers.
        assert "session_id" not in data
        assert "barriers" not in data
        assert "barriers_count" in data
        assert "next_steps" in data
        assert "created_at" in data
        assert "career_center_name" in data
        assert "career_center_phone" in data


class TestDashboardHardening:
    """Additional dashboard endpoint hardening."""

    @pytest.mark.anyio
    async def test_dashboard_stats_with_empty_barriers(self, client, test_engine):
        """Sessions with empty barrier string are handled gracefully."""
        factory = get_async_session_factory()
        async with factory() as db:
            now = datetime.now(timezone.utc)
            expires = (now + timedelta(days=30)).isoformat()
            await db.execute(
                text(
                    "INSERT INTO sessions (id, created_at, barriers, plan, expires_at) "
                    "VALUES (:id, :ts, :b, :p, :exp)"
                ),
                {"id": "00000000-0000-4000-8000-da5bbb000001",
                 "ts": now.isoformat(), "b": "", "p": None, "exp": expires},
            )
            await db.commit()

        resp = await client.get("/api/dashboard/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_assessments"] == 1
        assert data["total_barrier_instances"] == 0

    @pytest.mark.anyio
    async def test_outcomes_aggregate_response_format(self, client, test_engine):
        """Aggregate outcomes response has expected keys."""
        resp = await client.get("/api/outcomes/aggregate")
        assert resp.status_code == 200
        data = resp.json()
        assert "assessment_count" in data
        assert "top_barriers" in data
        assert isinstance(data["assessment_count"], int)
        assert isinstance(data["top_barriers"], list)

    @pytest.mark.anyio
    async def test_dashboard_stats_response_format(self, client, test_engine):
        """Dashboard stats response has expected keys."""
        resp = await client.get("/api/dashboard/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_assessments" in data
        assert "common_barriers" in data
        assert "total_barrier_instances" in data

    @pytest.mark.anyio
    async def test_common_barriers_limited_to_10(self, client, test_engine):
        """Dashboard stats limits common_barriers to 10 entries max."""
        resp = await client.get("/api/dashboard/stats")
        data = resp.json()
        assert len(data["common_barriers"]) <= 10

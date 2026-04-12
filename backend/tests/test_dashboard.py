"""Tests for case manager dashboard and aggregate outcomes endpoints."""

import json
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text

from app.core.database import get_async_session_factory


async def _seed_sessions(test_engine, count: int = 3) -> None:
    """Insert several sessions for aggregate stats."""
    factory = get_async_session_factory()
    async with factory() as db:
        now = datetime.now(timezone.utc)
        expires = (now + timedelta(days=30)).isoformat()
        for i in range(count):
            sid = f"00000000-0000-4000-8000-da5a0000000{i}"
            barriers = json.dumps(["credit", "transportation"] if i % 2 == 0 else ["childcare"])
            plan = json.dumps({"plan_id": f"p{i}", "session_id": sid, "barriers": [], "immediate_next_steps": []})
            await db.execute(
                text(
                    "INSERT INTO sessions (id, created_at, barriers, plan, expires_at) "
                    "VALUES (:id, :ts, :b, :p, :exp)"
                ),
                {"id": sid, "ts": now.isoformat(), "b": barriers, "p": plan, "exp": expires},
            )
        await db.commit()


class TestDashboardStats:
    """GET /api/dashboard/stats — aggregate metrics."""

    @pytest.mark.anyio
    async def test_returns_stats(self, client, test_engine):
        await _seed_sessions(test_engine, 5)
        resp = await client.get("/api/dashboard/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_assessments"] == 5
        assert "common_barriers" in data
        assert isinstance(data["common_barriers"], list)

    @pytest.mark.anyio
    async def test_empty_db_returns_zero(self, client, test_engine):
        resp = await client.get("/api/dashboard/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_assessments"] == 0


class TestAggregateOutcomes:
    """GET /api/outcomes/aggregate — anonymized aggregate display."""

    @pytest.mark.anyio
    async def test_returns_aggregate(self, client, test_engine):
        await _seed_sessions(test_engine, 3)
        resp = await client.get("/api/outcomes/aggregate")
        assert resp.status_code == 200
        data = resp.json()
        assert data["assessment_count"] == 3
        assert "top_barriers" in data


class TestDashboardAggregateAccuracy:
    """Verify aggregate computation accuracy."""

    @pytest.mark.anyio
    async def test_barrier_counts_accurate(self, client, test_engine):
        """Barrier counts reflect actual data across sessions."""
        await _seed_sessions(test_engine, 5)
        resp = await client.get("/api/dashboard/stats")
        data = resp.json()
        # 5 sessions: indices 0,2,4 have ["credit","transportation"], 1,3 have ["childcare"]
        barrier_map = {b["barrier"]: b["count"] for b in data["common_barriers"]}
        assert barrier_map.get("credit", 0) == 3
        assert barrier_map.get("transportation", 0) == 3
        assert barrier_map.get("childcare", 0) == 2

    @pytest.mark.anyio
    async def test_total_barrier_instances(self, client, test_engine):
        """Total barrier instances = sum of all barriers across sessions."""
        await _seed_sessions(test_engine, 5)
        resp = await client.get("/api/dashboard/stats")
        data = resp.json()
        # 3 sessions with 2 barriers + 2 sessions with 1 barrier = 8
        assert data["total_barrier_instances"] == 8

    @pytest.mark.anyio
    async def test_empty_db_aggregate_outcomes(self, client, test_engine):
        """Empty DB returns zero count and empty top_barriers."""
        resp = await client.get("/api/outcomes/aggregate")
        data = resp.json()
        assert data["assessment_count"] == 0
        assert data["top_barriers"] == []

    @pytest.mark.anyio
    async def test_sessions_with_malformed_barriers(self, client, test_engine):
        """Sessions with empty or malformed barrier data are handled gracefully."""
        factory = get_async_session_factory()
        async with factory() as db:
            now = datetime.now(timezone.utc)
            expires = (now + timedelta(days=30)).isoformat()
            # Session with empty barrier string
            await db.execute(
                text(
                    "INSERT INTO sessions (id, created_at, barriers, plan, expires_at) "
                    "VALUES (:id, :ts, :b, :p, :exp)"
                ),
                {"id": "00000000-0000-4000-8000-da5anull0001",
                 "ts": now.isoformat(), "b": "", "p": None, "exp": expires},
            )
            # Session with malformed JSON barriers
            await db.execute(
                text(
                    "INSERT INTO sessions (id, created_at, barriers, plan, expires_at) "
                    "VALUES (:id, :ts, :b, :p, :exp)"
                ),
                {"id": "00000000-0000-4000-8000-da5anull0002",
                 "ts": now.isoformat(), "b": "not-json", "p": None, "exp": expires},
            )
            await db.commit()

        resp = await client.get("/api/dashboard/stats")
        assert resp.status_code == 200
        data = resp.json()
        # 2 sessions counted but 0 valid barriers
        assert data["total_assessments"] == 2
        assert data["total_barrier_instances"] == 0

    @pytest.mark.anyio
    async def test_top_barriers_limited_to_5(self, client, test_engine):
        """Aggregate outcomes returns at most 5 top barriers."""
        await _seed_sessions(test_engine, 10)
        resp = await client.get("/api/outcomes/aggregate")
        data = resp.json()
        assert len(data["top_barriers"]) <= 5

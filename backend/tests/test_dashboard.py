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

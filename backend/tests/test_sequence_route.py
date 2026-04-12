"""Tests for barrier sequence endpoint — GET /api/plan/{session_id}/sequence."""

import json
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text

from app.core.database import get_async_session_factory


async def _seed_session_with_barriers(
    test_engine, session_id: str, barriers: list[str], *, auth_token: str,
) -> str:
    """Insert session with barriers and plan. Return the auth token."""
    factory = get_async_session_factory()
    async with factory() as db:
        now = datetime.now(timezone.utc)
        expires = (now + timedelta(days=30)).isoformat()
        plan = json.dumps({
            "plan_id": "test", "session_id": session_id,
            "barriers": [], "immediate_next_steps": ["Go"],
        })
        await db.execute(
            text(
                "INSERT INTO sessions (id, created_at, barriers, plan, expires_at) "
                "VALUES (:id, :ts, :b, :p, :exp)"
            ),
            {
                "id": session_id, "ts": now.isoformat(),
                "b": json.dumps(barriers), "p": plan, "exp": expires,
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
    return auth_token


class TestSequenceEndpoint:
    """GET /api/plan/{session_id}/sequence."""

    @pytest.mark.anyio
    async def test_returns_ordered_steps(self, client, test_engine):
        sid = "00000000-0000-4000-8000-5e00e0000001"
        tok = await _seed_session_with_barriers(
            test_engine, sid, ["criminal_record", "childcare", "credit"],
            auth_token="seq-tok-1",
        )
        resp = await client.get(f"/api/plan/{sid}/sequence?token={tok}")
        assert resp.status_code == 200
        data = resp.json()
        assert "steps" in data
        assert data["total_barriers"] == 3
        # Steps should be ordered
        orders = [s["order"] for s in data["steps"]]
        assert orders == sorted(orders)

    @pytest.mark.anyio
    async def test_empty_barriers_returns_empty(self, client, test_engine):
        sid = "00000000-0000-4000-8000-5e00e0000002"
        tok = await _seed_session_with_barriers(
            test_engine, sid, [], auth_token="seq-tok-2",
        )
        resp = await client.get(f"/api/plan/{sid}/sequence?token={tok}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["steps"] == []
        assert data["total_barriers"] == 0

    @pytest.mark.anyio
    async def test_invalid_token_returns_401(self, client, test_engine):
        resp = await client.get(
            "/api/plan/00000000-0000-4000-8000-5e00e0000003/sequence?token=bad"
        )
        assert resp.status_code == 401

    @pytest.mark.anyio
    async def test_steps_contain_unlocks(self, client, test_engine):
        sid = "00000000-0000-4000-8000-5e00e0000004"
        tok = await _seed_session_with_barriers(
            test_engine, sid, ["criminal_record", "childcare"],
            auth_token="seq-tok-4",
        )
        resp = await client.get(f"/api/plan/{sid}/sequence?token={tok}")
        data = resp.json()
        for step in data["steps"]:
            assert "unlocks" in step
            assert "barrier_name" in step
            assert "category" in step

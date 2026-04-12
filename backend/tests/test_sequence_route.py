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

    @pytest.mark.anyio
    async def test_single_barrier(self, client, test_engine):
        """A single barrier produces exactly one step."""
        sid = "00000000-0000-4000-8000-5e00e0000005"
        tok = await _seed_session_with_barriers(
            test_engine, sid, ["credit"],
            auth_token="seq-tok-5",
        )
        resp = await client.get(f"/api/plan/{sid}/sequence?token={tok}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_barriers"] == 1
        assert len(data["steps"]) == 1
        assert data["steps"][0]["barrier_id"] == "credit"

    @pytest.mark.anyio
    async def test_all_seven_barrier_types(self, client, test_engine):
        """All 7 standard barrier types are accepted and sequenced."""
        sid = "00000000-0000-4000-8000-5e00e0000006"
        all_barriers = [
            "criminal_record", "credit", "transportation",
            "childcare", "housing", "health", "training",
        ]
        tok = await _seed_session_with_barriers(
            test_engine, sid, all_barriers, auth_token="seq-tok-6",
        )
        resp = await client.get(f"/api/plan/{sid}/sequence?token={tok}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_barriers"] == 7
        assert len(data["steps"]) == 7
        returned_ids = {s["barrier_id"] for s in data["steps"]}
        assert returned_ids == set(all_barriers)

    @pytest.mark.anyio
    async def test_unknown_barrier_excluded(self, client, test_engine):
        """Barriers not in the graph mapping are silently excluded."""
        sid = "00000000-0000-4000-8000-5e00e0000007"
        tok = await _seed_session_with_barriers(
            test_engine, sid, ["credit", "unknown_type"],
            auth_token="seq-tok-7",
        )
        resp = await client.get(f"/api/plan/{sid}/sequence?token={tok}")
        assert resp.status_code == 200
        data = resp.json()
        # unknown_type is not mapped, so only credit appears
        returned_ids = [s["barrier_id"] for s in data["steps"]]
        assert "credit" in returned_ids
        assert "unknown_type" not in returned_ids

    @pytest.mark.anyio
    async def test_no_cycles_for_standard_barriers(self, client, test_engine):
        """Standard barrier sets should not produce cycles."""
        sid = "00000000-0000-4000-8000-5e00e0000008"
        tok = await _seed_session_with_barriers(
            test_engine, sid, ["criminal_record", "credit", "transportation"],
            auth_token="seq-tok-8",
        )
        resp = await client.get(f"/api/plan/{sid}/sequence?token={tok}")
        data = resp.json()
        assert data["has_cycles"] is False

    @pytest.mark.anyio
    async def test_session_not_found_returns_404(self, client, test_engine):
        """Requesting sequence for non-existent session returns error."""
        resp = await client.get(
            "/api/plan/00000000-0000-4000-8000-5e00e0000099/sequence?token=bad"
        )
        assert resp.status_code in (401, 404)

    @pytest.mark.anyio
    async def test_response_includes_estimated_total_weeks(self, client, test_engine):
        """Sequence response includes an estimated total timeline in weeks."""
        sid = "00000000-0000-4000-8000-5e00e000000a"
        tok = await _seed_session_with_barriers(
            test_engine, sid, ["criminal_record", "credit"],
            auth_token="seq-tok-a",
        )
        resp = await client.get(f"/api/plan/{sid}/sequence?token={tok}")
        data = resp.json()
        assert "estimated_total_weeks" in data
        assert isinstance(data["estimated_total_weeks"], int)
        assert data["estimated_total_weeks"] > 0

    @pytest.mark.anyio
    async def test_steps_include_estimated_weeks(self, client, test_engine):
        """Each step includes an estimated_weeks field."""
        sid = "00000000-0000-4000-8000-5e00e000000b"
        tok = await _seed_session_with_barriers(
            test_engine, sid, ["credit", "housing"],
            auth_token="seq-tok-b",
        )
        resp = await client.get(f"/api/plan/{sid}/sequence?token={tok}")
        data = resp.json()
        for step in data["steps"]:
            assert "estimated_weeks" in step
            assert isinstance(step["estimated_weeks"], int)
            assert step["estimated_weeks"] > 0

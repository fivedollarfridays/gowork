"""Tests for the 'What Happens If' multi-barrier simulator endpoint."""

import json
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text

from app.core.database import get_async_session_factory


async def _seed_session(
    test_engine, session_id: str, barriers: list[str], *, auth_token: str,
) -> str:
    """Insert session with barriers and plan. Return auth token."""
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
            {"id": session_id, "ts": now.isoformat(), "b": json.dumps(barriers), "p": plan, "exp": expires},
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


class TestSimulateEndpoint:
    """POST /api/simulate — multi-barrier impact simulation."""

    @pytest.mark.anyio
    async def test_resolving_barriers_returns_impact(self, client, test_engine):
        sid = "00000000-0000-4000-8000-51a000000001"
        tok = await _seed_session(
            test_engine, sid,
            ["criminal_record", "childcare", "credit"],
            auth_token="sim-tok-1",
        )
        resp = await client.post(
            f"/api/simulate?token={tok}",
            json={"session_id": sid, "resolved_barriers": ["criminal_record"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "barriers_remaining" in data
        assert "barriers_resolved" in data
        assert "unlocked_barriers" in data
        assert "jobs_unlocked_estimate" in data
        assert data["barriers_resolved"] == ["criminal_record"]

    @pytest.mark.anyio
    async def test_no_resolved_returns_baseline(self, client, test_engine):
        sid = "00000000-0000-4000-8000-51a000000002"
        tok = await _seed_session(
            test_engine, sid,
            ["credit", "transportation"],
            auth_token="sim-tok-2",
        )
        resp = await client.post(
            f"/api/simulate?token={tok}",
            json={"session_id": sid, "resolved_barriers": []},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["barriers_remaining"]) == 2
        assert data["barriers_resolved"] == []

    @pytest.mark.anyio
    async def test_resolve_all_barriers(self, client, test_engine):
        sid = "00000000-0000-4000-8000-51a000000003"
        tok = await _seed_session(
            test_engine, sid,
            ["credit", "childcare"],
            auth_token="sim-tok-3",
        )
        resp = await client.post(
            f"/api/simulate?token={tok}",
            json={"session_id": sid, "resolved_barriers": ["credit", "childcare"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["barriers_remaining"]) == 0

    @pytest.mark.anyio
    async def test_invalid_token_returns_401(self, client, test_engine):
        resp = await client.post(
            "/api/simulate?token=bad-token",
            json={
                "session_id": "00000000-0000-4000-8000-51a000000004",
                "resolved_barriers": [],
            },
        )
        assert resp.status_code == 401


class TestSimulateEdgeCases:
    """Edge cases and enhancements for the simulator."""

    @pytest.mark.anyio
    async def test_all_seven_barrier_types(self, client, test_engine):
        """Resolving all 7 barriers returns impact for each."""
        sid = "00000000-0000-4000-8000-51a000000005"
        all_barriers = [
            "criminal_record", "credit", "transportation",
            "childcare", "housing", "health", "training",
        ]
        tok = await _seed_session(
            test_engine, sid, all_barriers, auth_token="sim-tok-5",
        )
        resp = await client.post(
            f"/api/simulate?token={tok}",
            json={"session_id": sid, "resolved_barriers": all_barriers},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["barriers_remaining"]) == 0
        assert data["jobs_unlocked_estimate"] > 0
        assert len(data["benefits_unlocked"]) > 0

    @pytest.mark.anyio
    async def test_unknown_barrier_type_gets_default_estimate(self, client, test_engine):
        """Unknown barrier types get a default jobs estimate (3)."""
        sid = "00000000-0000-4000-8000-51a000000006"
        tok = await _seed_session(
            test_engine, sid, ["credit", "unknown_thing"],
            auth_token="sim-tok-6",
        )
        resp = await client.post(
            f"/api/simulate?token={tok}",
            json={"session_id": sid, "resolved_barriers": ["unknown_thing"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        # Default is 3 jobs for unknown barriers
        assert data["jobs_unlocked_estimate"] == 3

    @pytest.mark.anyio
    async def test_benefits_per_barrier_type(self, client, test_engine):
        """Each resolved barrier type yields specific benefits."""
        sid = "00000000-0000-4000-8000-51a000000007"
        tok = await _seed_session(
            test_engine, sid, ["childcare", "transportation"],
            auth_token="sim-tok-7",
        )
        resp = await client.post(
            f"/api/simulate?token={tok}",
            json={"session_id": sid, "resolved_barriers": ["childcare"]},
        )
        data = resp.json()
        assert "Childcare subsidy" in data["benefits_unlocked"]
        assert "Head Start" in data["benefits_unlocked"]

    @pytest.mark.anyio
    async def test_sequence_after_has_only_remaining(self, client, test_engine):
        """The sequence_after field reflects only remaining barriers."""
        sid = "00000000-0000-4000-8000-51a000000008"
        tok = await _seed_session(
            test_engine, sid, ["criminal_record", "credit", "transportation"],
            auth_token="sim-tok-8",
        )
        resp = await client.post(
            f"/api/simulate?token={tok}",
            json={"session_id": sid, "resolved_barriers": ["criminal_record"]},
        )
        data = resp.json()
        after_ids = {s["barrier_id"] for s in data["sequence_after"]["steps"]}
        assert "criminal_record" not in after_ids
        assert "credit" in after_ids
        assert "transportation" in after_ids

    @pytest.mark.anyio
    async def test_response_includes_confidence(self, client, test_engine):
        """Response includes confidence level for impact estimates."""
        sid = "00000000-0000-4000-8000-51a000000009"
        tok = await _seed_session(
            test_engine, sid, ["credit", "transportation"],
            auth_token="sim-tok-9",
        )
        resp = await client.post(
            f"/api/simulate?token={tok}",
            json={"session_id": sid, "resolved_barriers": ["credit"]},
        )
        data = resp.json()
        assert "confidence" in data
        assert data["confidence"] in ("low", "medium", "high")

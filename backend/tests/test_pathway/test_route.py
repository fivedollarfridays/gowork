"""Tests for the pathway API endpoint."""

import json
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text

from app.core.database import get_async_session_factory


async def _seed_session_with_benefits(
    test_engine, session_id: str, barriers: list[str],
    auth_token: str, benefits: dict | None = None,
) -> str:
    """Insert session with barriers and benefits profile."""
    factory = get_async_session_factory()
    async with factory() as db:
        now = datetime.now(timezone.utc)
        expires = (now + timedelta(days=30)).isoformat()
        plan = json.dumps({
            "plan_id": "test", "session_id": session_id,
            "barriers": [], "immediate_next_steps": ["Go"],
        })
        benefits_json = json.dumps(benefits) if benefits else None
        await db.execute(
            text(
                "INSERT INTO sessions "
                "(id, created_at, barriers, plan, expires_at, benefits_profile) "
                "VALUES (:id, :ts, :b, :p, :exp, :bp)"
            ),
            {
                "id": session_id,
                "ts": now.isoformat(),
                "b": json.dumps(barriers),
                "p": plan,
                "exp": expires,
                "bp": benefits_json,
            },
        )
        await db.execute(
            text(
                "INSERT INTO feedback_tokens "
                "(token, session_id, created_at, expires_at) "
                "VALUES (:tok, :sid, :ts, :exp)"
            ),
            {
                "tok": auth_token,
                "sid": session_id,
                "ts": now.isoformat(),
                "exp": expires,
            },
        )
        await db.commit()
    return auth_token


class TestPathwayEndpoint:
    """POST /api/pathway -- career pathway generation."""

    @pytest.mark.anyio
    async def test_generates_pathways(self, client, test_engine):
        sid = "00000000-0000-4000-8000-aa0000000001"
        tok = await _seed_session_with_benefits(
            test_engine, sid,
            ["criminal_record", "transportation"],
            auth_token="path-tok-1",
            benefits={
                "household_size": 3,
                "current_monthly_income": 1200.0,
                "enrolled_programs": ["SNAP"],
                "dependents_under_6": 1,
                "dependents_6_to_17": 0,
                "state": "TX",
            },
        )
        resp = await client.post(
            f"/api/pathway?token={tok}",
            json={
                "session_id": sid,
                "current_wage": 0.0,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "pathways" in data
        assert len(data["pathways"]) >= 1
        assert "current_wage" in data
        assert "barriers_active" in data
        assert "best_pathway" in data

    @pytest.mark.anyio
    async def test_pathway_without_benefits(self, client, test_engine):
        sid = "00000000-0000-4000-8000-aa0000000002"
        tok = await _seed_session_with_benefits(
            test_engine, sid,
            ["criminal_record"],
            auth_token="path-tok-2",
        )
        resp = await client.post(
            f"/api/pathway?token={tok}",
            json={
                "session_id": sid,
                "current_wage": 10.0,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["pathways"]) >= 1

    @pytest.mark.anyio
    async def test_pathway_session_not_found(self, client, test_engine):
        resp = await client.post(
            "/api/pathway?token=fake-tok",
            json={
                "session_id": "00000000-0000-4000-8000-aa0000000099",
                "current_wage": 10.0,
            },
        )
        assert resp.status_code in (401, 404)

    @pytest.mark.anyio
    async def test_pathway_steps_have_net_income(self, client, test_engine):
        sid = "00000000-0000-4000-8000-aa0000000003"
        tok = await _seed_session_with_benefits(
            test_engine, sid,
            ["criminal_record"],
            auth_token="path-tok-3",
            benefits={
                "household_size": 2,
                "current_monthly_income": 1000.0,
                "enrolled_programs": ["SNAP"],
                "dependents_under_6": 0,
                "dependents_6_to_17": 1,
                "state": "TX",
            },
        )
        resp = await client.post(
            f"/api/pathway?token={tok}",
            json={"session_id": sid, "current_wage": 8.0},
        )
        assert resp.status_code == 200
        data = resp.json()
        best = data["best_pathway"]
        assert best is not None
        for step in best["steps"]:
            assert step["net_monthly_income"] is not None
            assert step["net_monthly_income"] > 0

"""Tests for the unified Plan Intelligence endpoint.

GET /api/plan/{session_id}/intelligence returns EVERYTHING a frontend
needs in one call: barriers (sequenced), pathway (calibrated), cliff
analysis, and community stats.
"""

import json
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text

from app.core.database import get_async_session_factory


async def _seed_session(
    test_engine,
    session_id: str,
    barriers: list[str],
    auth_token: str,
    *,
    benefits_profile: dict | None = None,
) -> str:
    """Insert a session with barriers, plan, auth token, and optional benefits profile."""
    factory = get_async_session_factory()
    async with factory() as db:
        now = datetime.now(timezone.utc)
        expires = (now + timedelta(days=30)).isoformat()
        plan = json.dumps({
            "plan_id": "test", "session_id": session_id,
            "barriers": [], "immediate_next_steps": ["Go"],
        })
        bp_json = json.dumps(benefits_profile) if benefits_profile else None
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
                "bp": bp_json,
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


async def _seed_feedback_session(
    test_engine,
    session_id: str,
    barriers: list[str],
    outcomes: list[str],
    plan_accuracy: int,
) -> None:
    """Seed a session AND feedback for populating intelligence data."""
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
                "id": session_id,
                "ts": now.isoformat(),
                "b": json.dumps(barriers),
                "exp": expires,
            },
        )
        await db.execute(
            text(
                "INSERT INTO visit_feedback "
                "(session_id, submitted_at, made_it_to_center, outcomes, plan_accuracy) "
                "VALUES (:sid, '2026-03-01T00:00:00', 1, :outcomes, :accuracy)"
            ),
            {
                "sid": session_id,
                "outcomes": json.dumps(outcomes),
                "accuracy": plan_accuracy,
            },
        )
        await db.commit()


class TestPlanIntelligenceEndpoint:
    """GET /api/plan/{session_id}/intelligence -- unified intelligence."""

    @pytest.mark.anyio
    async def test_returns_complete_intelligence(self, client, test_engine):
        """Single endpoint returns barriers + pathway + cliff + community data."""
        sid = "55555555-5555-5555-5555-000000000001"
        tok = await _seed_session(
            test_engine, sid,
            ["criminal_record", "credit", "transportation"],
            auth_token="intel-tok-1",
        )
        resp = await client.get(
            f"/api/plan/{sid}/intelligence?token={tok}&current_wage=10.0",
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "barriers" in data
        assert "pathway" in data
        assert "cliff_analysis" in data
        assert "community_intelligence" in data

    @pytest.mark.anyio
    async def test_barriers_section_has_sequence(self, client, test_engine):
        """Barriers section should include sequenced steps and total weeks."""
        sid = "55555555-5555-5555-5555-000000000002"
        tok = await _seed_session(
            test_engine, sid,
            ["criminal_record", "credit"],
            auth_token="intel-tok-2",
        )
        resp = await client.get(
            f"/api/plan/{sid}/intelligence?token={tok}&current_wage=10.0",
        )
        data = resp.json()
        barriers = data["barriers"]
        assert "steps" in barriers
        assert "estimated_total_weeks" in barriers
        assert len(barriers["steps"]) == 2

    @pytest.mark.anyio
    async def test_pathway_section_has_strategies(self, client, test_engine):
        """Pathway section should include multiple ranked strategies."""
        sid = "55555555-5555-5555-5555-000000000003"
        tok = await _seed_session(
            test_engine, sid,
            ["criminal_record"],
            auth_token="intel-tok-3",
        )
        resp = await client.get(
            f"/api/plan/{sid}/intelligence?token={tok}&current_wage=10.0",
        )
        data = resp.json()
        pathway = data["pathway"]
        assert "pathways" in pathway
        assert len(pathway["pathways"]) > 0
        assert "best_pathway" in pathway

    @pytest.mark.anyio
    async def test_cliff_analysis_section(self, client, test_engine):
        """Cliff analysis section should include wage steps and cliff points."""
        sid = "55555555-5555-5555-5555-000000000004"
        bp = {
            "household_size": 3,
            "annual_income": 20000,
            "enrolled_programs": ["SNAP"],
        }
        tok = await _seed_session(
            test_engine, sid,
            ["credit"],
            auth_token="intel-tok-4",
            benefits_profile=bp,
        )
        resp = await client.get(
            f"/api/plan/{sid}/intelligence?token={tok}&current_wage=10.0",
        )
        data = resp.json()
        cliff = data["cliff_analysis"]
        assert "wage_steps" in cliff
        assert "cliff_points" in cliff
        assert "current_net_monthly" in cliff

    @pytest.mark.anyio
    async def test_community_intelligence_with_feedback(self, client, test_engine):
        """Community intelligence reflects real feedback data."""
        # Seed 4 feedback sessions for criminal_record
        for i in range(4):
            fb_sid = f"66666666-6666-6666-6666-{i:012d}"
            await _seed_feedback_session(
                test_engine, fb_sid,
                ["criminal_record"], ["criminal_record"], 4,
            )

        sid = "55555555-5555-5555-5555-000000000005"
        tok = await _seed_session(
            test_engine, sid,
            ["criminal_record"],
            auth_token="intel-tok-5",
        )
        resp = await client.get(
            f"/api/plan/{sid}/intelligence?token={tok}&current_wage=10.0",
        )
        data = resp.json()
        ci = data["community_intelligence"]
        assert ci["total_feedback"] == 4
        assert "criminal_record" in ci["calibrated_barriers"]

    @pytest.mark.anyio
    async def test_cold_start_community_intelligence(self, client, test_engine):
        """On cold start, community intelligence has zero feedback."""
        sid = "55555555-5555-5555-5555-000000000006"
        tok = await _seed_session(
            test_engine, sid,
            ["credit"],
            auth_token="intel-tok-6",
        )
        resp = await client.get(
            f"/api/plan/{sid}/intelligence?token={tok}&current_wage=10.0",
        )
        data = resp.json()
        ci = data["community_intelligence"]
        assert ci["total_feedback"] == 0
        assert ci["calibrated_barriers"] == {}

    @pytest.mark.anyio
    async def test_invalid_token_returns_401(self, client, test_engine):
        """Invalid auth token returns 401."""
        resp = await client.get(
            "/api/plan/55555555-5555-5555-5555-000000000007/intelligence"
            "?token=bad-token&current_wage=10.0",
        )
        assert resp.status_code == 401

    @pytest.mark.anyio
    async def test_session_not_found_returns_404(self, client, test_engine):
        """Non-existent session returns 404."""
        resp = await client.get(
            "/api/plan/55555555-5555-5555-5555-000000000099/intelligence"
            "?token=any&current_wage=10.0",
        )
        assert resp.status_code in (401, 404)

    @pytest.mark.anyio
    async def test_improvements_from_defaults_shown(self, client, test_engine):
        """community_intelligence shows improvements_from_defaults."""
        sid = "55555555-5555-5555-5555-000000000008"
        tok = await _seed_session(
            test_engine, sid,
            ["criminal_record"],
            auth_token="intel-tok-8",
        )
        resp = await client.get(
            f"/api/plan/{sid}/intelligence?token={tok}&current_wage=10.0",
        )
        data = resp.json()
        ci = data["community_intelligence"]
        assert "improvements_from_defaults" in ci

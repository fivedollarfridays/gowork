"""Tests for the insights section in the Plan Intelligence endpoint.

Verifies that GET /api/plan/{session_id}/intelligence now includes
a 'insights' section with personalized community insight messages.
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
) -> str:
    """Insert a session with barriers, plan, and auth token."""
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
                "INSERT INTO sessions "
                "(id, created_at, barriers, plan, expires_at) "
                "VALUES (:id, :ts, :b, :p, :exp)"
            ),
            {
                "id": session_id,
                "ts": now.isoformat(),
                "b": json.dumps(barriers),
                "p": plan,
                "exp": expires,
            },
        )
        await db.execute(
            text(
                "INSERT INTO feedback_tokens "
                "(token, session_id, created_at, expires_at) "
                "VALUES (:tok, :sid, :ts, :exp)"
            ),
            {"tok": auth_token, "sid": session_id,
             "ts": now.isoformat(), "exp": expires},
        )
        await db.commit()
    return auth_token


async def _seed_feedback(test_engine, session_id, barriers, outcomes, accuracy):
    """Seed a feedback session for intelligence data."""
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
                "id": session_id, "ts": now.isoformat(),
                "b": json.dumps(barriers), "exp": expires,
            },
        )
        await db.execute(
            text(
                "INSERT INTO visit_feedback "
                "(session_id, submitted_at, made_it_to_center, "
                "outcomes, plan_accuracy) "
                "VALUES (:sid, :ts, 1, :outcomes, :accuracy)"
            ),
            {
                "sid": session_id, "ts": now.isoformat(),
                "outcomes": json.dumps(outcomes), "accuracy": accuracy,
            },
        )
        await db.commit()


class TestPlanIntelligenceInsightsSection:
    """Plan Intelligence endpoint includes insights section."""

    @pytest.mark.anyio
    async def test_response_includes_insights_key(self, client, test_engine):
        """The unified response has an 'insights' key."""
        sid = "99999999-9999-9999-9999-000000000001"
        tok = await _seed_session(
            test_engine, sid,
            ["criminal_record"], "pi-insights-tok-1",
        )
        resp = await client.get(
            f"/api/plan/{sid}/intelligence?token={tok}&current_wage=10.0",
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "insights" in data

    @pytest.mark.anyio
    async def test_insights_section_is_list(self, client, test_engine):
        """The insights section is a list of insight objects."""
        sid = "99999999-9999-9999-9999-000000000002"
        tok = await _seed_session(
            test_engine, sid,
            ["credit", "transportation"], "pi-insights-tok-2",
        )
        resp = await client.get(
            f"/api/plan/{sid}/intelligence?token={tok}&current_wage=10.0",
        )
        data = resp.json()
        assert isinstance(data["insights"], list)

    @pytest.mark.anyio
    async def test_insights_with_feedback_data(self, client, test_engine):
        """With feedback data, insights reference calibrated stats."""
        for i in range(10):
            fb_sid = f"aaaaaaaa-aaaa-aaaa-aaaa-{i:012d}"
            await _seed_feedback(
                test_engine, fb_sid,
                ["criminal_record"], ["criminal_record"], 4,
            )

        sid = "99999999-9999-9999-9999-000000000003"
        tok = await _seed_session(
            test_engine, sid,
            ["criminal_record"], "pi-insights-tok-3",
        )
        resp = await client.get(
            f"/api/plan/{sid}/intelligence?token={tok}&current_wage=10.0",
        )
        data = resp.json()
        insights = data["insights"]
        assert len(insights) >= 1
        # Should have resolution_time and success_rate insights
        metric_types = {i["metric_type"] for i in insights}
        assert "resolution_time" in metric_types

    @pytest.mark.anyio
    async def test_cold_start_insights(self, client, test_engine):
        """On cold start, insights have encouraging first-user message."""
        sid = "99999999-9999-9999-9999-000000000004"
        tok = await _seed_session(
            test_engine, sid,
            ["housing"], "pi-insights-tok-4",
        )
        resp = await client.get(
            f"/api/plan/{sid}/intelligence?token={tok}&current_wage=10.0",
        )
        data = resp.json()
        insights = data["insights"]
        assert len(insights) >= 1
        assert "first" in insights[0]["message"].lower()

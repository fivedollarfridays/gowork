"""Integration tests: seed demo data -> request insights -> verify messages.

These tests run the demo seed to populate realistic barrier data,
then exercise the community insights pipeline end-to-end.
"""

import json
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text

from app.core.database import get_async_session_factory
from app.demo_seed import run_demo_seed


async def _create_session_with_token(
    test_engine,
    session_id: str,
    barriers: list[str],
    auth_token: str,
) -> str:
    """Insert a session with barriers + auth token for API testing."""
    factory = get_async_session_factory()
    async with factory() as db:
        now = datetime.now(timezone.utc)
        expires = (now + timedelta(days=30)).isoformat()
        plan = json.dumps({
            "plan_id": "test", "session_id": session_id,
            "barriers": [], "immediate_next_steps": ["Visit center"],
        })
        await db.execute(
            text(
                "INSERT INTO sessions "
                "(id, created_at, barriers, plan, expires_at, profile) "
                "VALUES (:id, :ts, :b, :p, :exp, :prof)"
            ),
            {
                "id": session_id,
                "ts": now.isoformat(),
                "b": json.dumps(barriers),
                "p": plan,
                "exp": expires,
                "prof": json.dumps({"zip_code": "76102"}),
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


class TestInsightsWithSeedData:
    """Integration: seed data -> insights pipeline -> verify messages."""

    @pytest.mark.anyio
    async def test_seeded_data_produces_insights(self, client, test_engine):
        """After seeding, insights endpoint returns non-empty insights."""
        factory = get_async_session_factory()
        async with factory() as db:
            await run_demo_seed(db)

        sid = "cccccccc-cccc-cccc-cccc-000000000001"
        tok = await _create_session_with_token(
            test_engine, sid,
            ["criminal_record", "transportation"], "seed-tok-1",
        )
        resp = await client.get(f"/api/insights/{sid}?token={tok}")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["insights"]) >= 1
        # Insights should NOT be cold-start since seed data exists
        assert "first" not in data["insights"][0]["message"].lower()

    @pytest.mark.anyio
    async def test_seeded_insights_reference_calibrated_stats(
        self, client, test_engine,
    ):
        """Insights from seeded data reference actual barrier stats."""
        factory = get_async_session_factory()
        async with factory() as db:
            await run_demo_seed(db)

        sid = "cccccccc-cccc-cccc-cccc-000000000002"
        tok = await _create_session_with_token(
            test_engine, sid,
            ["criminal_record"], "seed-tok-2",
        )
        resp = await client.get(f"/api/insights/{sid}?token={tok}")
        data = resp.json()
        insights = data["insights"]
        # Should have resolution time insight for criminal_record
        resolution = [
            i for i in insights if i["metric_type"] == "resolution_time"
        ]
        assert len(resolution) >= 1
        msg = resolution[0]["message"]
        # Message should contain a number (weeks estimate)
        assert any(c.isdigit() for c in msg)

    @pytest.mark.anyio
    async def test_seeded_plan_intelligence_has_insights(
        self, client, test_engine,
    ):
        """Plan intelligence endpoint includes insights after seeding."""
        factory = get_async_session_factory()
        async with factory() as db:
            await run_demo_seed(db)

        sid = "cccccccc-cccc-cccc-cccc-000000000003"
        tok = await _create_session_with_token(
            test_engine, sid,
            ["criminal_record", "credit", "childcare"], "seed-tok-3",
        )
        resp = await client.get(
            f"/api/plan/{sid}/intelligence?token={tok}&current_wage=10.0",
        )
        data = resp.json()
        assert "insights" in data
        assert len(data["insights"]) >= 1
        # With 3 barriers and seeded data, should get recommendation too
        metric_types = {i["metric_type"] for i in data["insights"]}
        assert "resolution_time" in metric_types

    @pytest.mark.anyio
    async def test_seeded_insights_are_deterministic(
        self, client, test_engine,
    ):
        """Two requests with same data produce identical insights."""
        factory = get_async_session_factory()
        async with factory() as db:
            await run_demo_seed(db)

        sid = "cccccccc-cccc-cccc-cccc-000000000004"
        tok = await _create_session_with_token(
            test_engine, sid,
            ["transportation", "credit"], "seed-tok-4",
        )
        resp1 = await client.get(f"/api/insights/{sid}?token={tok}")
        resp2 = await client.get(f"/api/insights/{sid}?token={tok}")
        assert resp1.json() == resp2.json()

    @pytest.mark.anyio
    async def test_carlos_persona_insights(self, client, test_engine):
        """Carlos (Fort Worth, criminal+childcare+credit) gets insights."""
        factory = get_async_session_factory()
        async with factory() as db:
            await run_demo_seed(db)

        sid = "cccccccc-cccc-cccc-cccc-000000000005"
        tok = await _create_session_with_token(
            test_engine, sid,
            ["criminal_record", "childcare", "credit"], "seed-tok-5",
        )
        resp = await client.get(f"/api/insights/{sid}?token={tok}")
        data = resp.json()
        insights = data["insights"]
        assert len(insights) >= 3  # At least resolution for each barrier
        # Check barrier coverage
        barrier_types = {i["barrier_type"] for i in insights}
        assert "criminal_record" in barrier_types

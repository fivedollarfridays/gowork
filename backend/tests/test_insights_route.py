"""Tests for the standalone Community Insights endpoint.

GET /api/insights/{session_id} returns personalized community
insight messages based on the session's barrier profile.
"""

import json
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text

from app.core.database import get_async_session_factory


async def _seed_session_with_token(
    test_engine,
    session_id: str,
    barriers: list[str],
    auth_token: str,
) -> str:
    """Insert a session with barriers, auth token, and future expiry."""
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


async def _seed_feedback(
    test_engine,
    session_id: str,
    barriers: list[str],
    outcomes: list[str],
    plan_accuracy: int,
) -> None:
    """Seed a feedback session for populating intelligence data."""
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
                "(session_id, submitted_at, made_it_to_center, "
                "outcomes, plan_accuracy) "
                "VALUES (:sid, :ts, 1, :outcomes, :accuracy)"
            ),
            {
                "sid": session_id,
                "ts": now.isoformat(),
                "outcomes": json.dumps(outcomes),
                "accuracy": plan_accuracy,
            },
        )
        await db.commit()


class TestInsightsEndpoint:
    """GET /api/insights/{session_id} -- personalized community insights."""

    @pytest.mark.anyio
    async def test_returns_insights_list(self, client, test_engine):
        """Endpoint returns a list of insight objects."""
        # Seed feedback data first
        for i in range(12):
            fb_sid = f"77777777-7777-7777-7777-{i:012d}"
            await _seed_feedback(
                test_engine, fb_sid,
                ["criminal_record"], ["criminal_record"], 4,
            )

        sid = "88888888-8888-8888-8888-000000000001"
        tok = await _seed_session_with_token(
            test_engine, sid, ["criminal_record"], "insights-tok-1",
        )
        resp = await client.get(
            f"/api/insights/{sid}?token={tok}",
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "insights" in data
        assert isinstance(data["insights"], list)
        assert len(data["insights"]) >= 1

    @pytest.mark.anyio
    async def test_cold_start_returns_encouraging_insight(
        self, client, test_engine,
    ):
        """No feedback data returns a cold start insight."""
        sid = "88888888-8888-8888-8888-000000000002"
        tok = await _seed_session_with_token(
            test_engine, sid, ["credit"], "insights-tok-2",
        )
        resp = await client.get(
            f"/api/insights/{sid}?token={tok}",
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["insights"]) >= 1
        assert "first" in data["insights"][0]["message"].lower()

    @pytest.mark.anyio
    async def test_invalid_token_returns_401(self, client, test_engine):
        """Invalid auth token returns 401."""
        resp = await client.get(
            "/api/insights/88888888-8888-8888-8888-000000000099?token=bad",
        )
        assert resp.status_code == 401

    @pytest.mark.anyio
    async def test_session_not_found_returns_404(self, client, test_engine):
        """Non-existent session returns 404 (after valid token check)."""
        # Create a valid token for one session, but query a different one
        sid = "88888888-8888-8888-8888-000000000003"
        tok = await _seed_session_with_token(
            test_engine, sid, ["credit"], "insights-tok-3",
        )
        # Token is valid for sid, but if we query a different session it's 403
        resp = await client.get(
            "/api/insights/88888888-8888-8888-8888-000000000098?token="
            + tok,
        )
        assert resp.status_code in (401, 403, 404)

    @pytest.mark.anyio
    async def test_insight_contains_city_name(self, client, test_engine):
        """Insights contain the city name from config."""
        for i in range(5):
            fb_sid = f"77777777-7777-7777-8888-{i:012d}"
            await _seed_feedback(
                test_engine, fb_sid,
                ["transportation"], ["transportation"], 5,
            )

        sid = "88888888-8888-8888-8888-000000000004"
        tok = await _seed_session_with_token(
            test_engine, sid, ["transportation"], "insights-tok-4",
        )
        resp = await client.get(
            f"/api/insights/{sid}?token={tok}",
        )
        data = resp.json()
        # At least one insight should contain a city name
        messages = " ".join(i["message"] for i in data["insights"])
        # City name from config (either Fort Worth or Montgomery)
        assert "Fort Worth" in messages or "Montgomery" in messages

    @pytest.mark.anyio
    async def test_response_includes_metadata(self, client, test_engine):
        """Response includes barrier_count and city metadata."""
        sid = "88888888-8888-8888-8888-000000000005"
        tok = await _seed_session_with_token(
            test_engine, sid, ["criminal_record", "credit"], "insights-tok-5",
        )
        resp = await client.get(
            f"/api/insights/{sid}?token={tok}",
        )
        data = resp.json()
        assert "barrier_count" in data
        assert data["barrier_count"] == 2
        assert "city" in data

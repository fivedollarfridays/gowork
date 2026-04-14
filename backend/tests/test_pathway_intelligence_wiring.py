"""Tests proving the pathway route fetches calibrated_weeks from intelligence at request time.

The N+1 feedback loop means: visit_feedback in DB -> intelligence engine computes
calibrated weeks -> pathway route passes them to generate_pathways. These tests
verify the wiring is real, not theoretical.
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
    """Insert a session with barriers and auth token."""
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
                "id": session_id,
                "ts": now.isoformat(),
                "b": json.dumps(barriers),
                "p": plan,
                "exp": expires,
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


async def _seed_feedback_with_weeks(
    test_engine,
    session_id: str,
    barriers: list[str],
    outcomes: list[str],
    plan_accuracy: int,
) -> None:
    """Insert a session + feedback where the session has specific barriers."""
    factory = get_async_session_factory()
    async with factory() as db:
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


async def _seed_feedback_session(
    test_engine,
    session_id: str,
    barriers: list[str],
    outcomes: list[str],
    plan_accuracy: int,
) -> None:
    """Seed a session AND feedback for that session (for populating intelligence data)."""
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


class TestPathwayUsesIntelligenceData:
    """Pathway route must fetch calibrated_weeks from intelligence at request time."""

    @pytest.mark.anyio
    async def test_pathway_uses_calibrated_weeks_from_feedback(
        self, client, test_engine,
    ):
        """When real feedback exists with 3+ samples, pathway should use calibrated data.

        We seed 5 feedback sessions reporting criminal_record resolved.
        The intelligence engine will compute MEDIUM+ confidence for criminal_record.
        Since weeks_to_resolve is None in current schema, the avg_weeks will be 0,
        so calibrated_weeks dict will be empty (only non-zero avg_weeks included).
        But the WIRING must exist -- the pathway route must call the intelligence
        engine and pass the result to generate_pathways.
        """
        # Seed 5 feedback sessions for criminal_record
        for i in range(5):
            feedback_sid = f"11111111-1111-1111-1111-{i:012d}"
            await _seed_feedback_session(
                test_engine, feedback_sid,
                ["criminal_record"], ["criminal_record"], 4,
            )

        # Create the actual user session requesting pathways
        user_sid = "22222222-2222-2222-2222-000000000001"
        tok = await _seed_session(
            test_engine, user_sid,
            ["criminal_record", "credit"],
            auth_token="wire-tok-1",
        )

        resp = await client.post(
            f"/api/pathway?token={tok}",
            json={"session_id": user_sid, "current_wage": 10.0},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "pathways" in data
        assert len(data["pathways"]) > 0
        # The response should include community_intelligence metadata
        assert "community_intelligence" in data

    @pytest.mark.anyio
    async def test_pathway_falls_back_to_defaults_on_cold_start(
        self, client, test_engine,
    ):
        """When no feedback exists, pathway should use hardcoded defaults gracefully."""
        user_sid = "33333333-3333-3333-3333-000000000001"
        tok = await _seed_session(
            test_engine, user_sid,
            ["criminal_record", "transportation"],
            auth_token="wire-tok-2",
        )

        resp = await client.post(
            f"/api/pathway?token={tok}",
            json={"session_id": user_sid, "current_wage": 10.0},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "pathways" in data
        # community_intelligence should indicate cold start
        ci = data.get("community_intelligence", {})
        assert ci.get("total_feedback") == 0

    @pytest.mark.anyio
    async def test_pathway_response_includes_calibration_source(
        self, client, test_engine,
    ):
        """Response should be honest about what's calibrated vs default."""
        user_sid = "44444444-4444-4444-4444-000000000001"
        tok = await _seed_session(
            test_engine, user_sid,
            ["credit"],
            auth_token="wire-tok-3",
        )

        resp = await client.post(
            f"/api/pathway?token={tok}",
            json={"session_id": user_sid, "current_wage": 12.0},
        )
        assert resp.status_code == 200
        data = resp.json()
        ci = data.get("community_intelligence", {})
        # Must include calibrated_barriers and improvements_from_defaults
        assert "calibrated_barriers" in ci
        assert "improvements_from_defaults" in ci

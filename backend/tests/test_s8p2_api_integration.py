"""API-level integration tests for S8 Phase 2.

Verifies that API routes correctly chain to their dependent modules,
exercising the full request/response cycle with real DB state.
"""

import json
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text

from app.core.database import get_async_session_factory


async def _seed_session(test_engine, sid, barriers, tok, *, bp=None):
    """Seed a session with plan, barriers, auth token."""
    factory = get_async_session_factory()
    async with factory() as db:
        now = datetime.now(timezone.utc)
        exp = (now + timedelta(days=30)).isoformat()
        plan = json.dumps({
            "plan_id": "api-test",
            "session_id": sid,
            "barriers": [{"type": b} for b in barriers],
            "immediate_next_steps": ["Visit career center"],
        })
        await db.execute(
            text(
                "INSERT INTO sessions "
                "(id, created_at, barriers, plan, expires_at, benefits_profile) "
                "VALUES (:id, :ts, :b, :p, :exp, :bp)"
            ),
            {
                "id": sid,
                "ts": now.isoformat(),
                "b": json.dumps(barriers),
                "p": plan,
                "exp": exp,
                "bp": json.dumps(bp) if bp else None,
            },
        )
        await db.execute(
            text(
                "INSERT INTO feedback_tokens "
                "(token, session_id, created_at, expires_at) "
                "VALUES (:tok, :sid, :ts, :exp)"
            ),
            {"tok": tok, "sid": sid, "ts": now.isoformat(), "exp": exp},
        )
        await db.commit()


async def _seed_feedback(test_engine, sid, barriers_json, outcomes_json, accuracy=4):
    """Seed visit_feedback for intelligence tests."""
    factory = get_async_session_factory()
    async with factory() as db:
        now = datetime.now(timezone.utc)
        exp = (now + timedelta(days=30)).isoformat()
        # Ensure session exists
        result = await db.execute(
            text("SELECT id FROM sessions WHERE id = :id"),
            {"id": sid},
        )
        if result.fetchone() is None:
            await db.execute(
                text(
                    "INSERT INTO sessions "
                    "(id, created_at, barriers, expires_at) "
                    "VALUES (:id, :ts, :b, :exp)"
                ),
                {
                    "id": sid,
                    "ts": now.isoformat(),
                    "b": barriers_json,
                    "exp": exp,
                },
            )
        await db.execute(
            text(
                "INSERT INTO visit_feedback "
                "(session_id, submitted_at, made_it_to_center, outcomes, plan_accuracy) "
                "VALUES (:sid, :ts, 1, :outcomes, :acc)"
            ),
            {
                "sid": sid,
                "ts": now.isoformat(),
                "outcomes": outcomes_json,
                "acc": accuracy,
            },
        )
        await db.commit()


# ---------------------------------------------------------------------------
# Intelligence -> API: with real DB feedback data
# ---------------------------------------------------------------------------

class TestIntelligenceAPI:
    """Intelligence API with actual visit_feedback in DB."""

    @pytest.mark.anyio
    async def test_intelligence_with_feedback_data(self, client, test_engine):
        """Intelligence endpoint returns calibrated data when feedback exists."""
        # Seed 5 feedback entries for criminal_record (MEDIUM confidence)
        for i in range(5):
            sid = f"00000000-0000-4000-8000-c00e000000{i:03d}"
            await _seed_feedback(
                test_engine, sid,
                json.dumps(["criminal_record"]),
                json.dumps(["criminal_record"]),
                accuracy=4,
            )

        r = await client.get("/api/intelligence/barriers")
        assert r.status_code == 200
        data = r.json()
        assert "barriers" in data
        assert "calibrated_weeks" in data
        assert "default_weeks" in data
        assert data["total_feedback_count"] >= 5

    @pytest.mark.anyio
    async def test_intelligence_empty_db(self, client, test_engine):
        """Intelligence endpoint returns defaults when no feedback exists."""
        r = await client.get("/api/intelligence/barriers")
        assert r.status_code == 200
        data = r.json()
        assert data["calibrated_weeks"] == {}
        assert data["confidence"] == "none"
        assert data["total_feedback_count"] == 0
        # default_weeks should still have all barrier types
        assert "criminal_record" in data["default_weeks"]


# ---------------------------------------------------------------------------
# Dashboard -> DB: stats from real sessions
# ---------------------------------------------------------------------------

class TestDashboardDB:
    """Dashboard returns real aggregate data from seeded sessions."""

    @pytest.mark.anyio
    async def test_dashboard_reflects_seeded_sessions(self, client, test_engine):
        """Dashboard stats count matches seeded session data."""
        # Seed 3 sessions with different barriers
        await _seed_session(
            test_engine,
            "00000000-0000-4000-8000-da0000000001",
            ["criminal_record", "credit"],
            "dash-tok-1",
        )
        await _seed_session(
            test_engine,
            "00000000-0000-4000-8000-da0000000002",
            ["transportation", "childcare", "credit"],
            "dash-tok-2",
        )
        await _seed_session(
            test_engine,
            "00000000-0000-4000-8000-da0000000003",
            ["housing"],
            "dash-tok-3",
        )

        r = await client.get("/api/dashboard/stats")
        assert r.status_code == 200
        data = r.json()
        assert data["total_assessments"] == 3
        # Total barrier instances: 2 + 3 + 1 = 6
        assert data["total_barrier_instances"] == 6
        # credit appears twice, should be in common_barriers
        barrier_names = [b["barrier"] for b in data["common_barriers"]]
        assert "credit" in barrier_names

    @pytest.mark.anyio
    async def test_outcomes_aggregate(self, client, test_engine):
        """Outcomes aggregate endpoint returns real data."""
        await _seed_session(
            test_engine,
            "00000000-0000-4000-8000-da0000000004",
            ["criminal_record", "credit", "transportation"],
            "dash-tok-4",
        )

        r = await client.get("/api/outcomes/aggregate")
        assert r.status_code == 200
        data = r.json()
        assert data["assessment_count"] >= 1
        assert "top_barriers" in data


# ---------------------------------------------------------------------------
# Simulate -> Sequencer: barrier toggles -> impact -> sequence_after
# ---------------------------------------------------------------------------

class TestSimulateSequencer:
    """Simulate endpoint chains to barrier sequencer correctly."""

    @pytest.mark.anyio
    async def test_simulate_sequence_after_reflects_remaining(
        self, client, test_engine,
    ):
        """sequence_after in simulate response has correct barrier order."""
        sid = "00000000-0000-4000-8000-a00000000001"
        tok = "sim-tok-1"
        barriers = ["criminal_record", "credit", "transportation", "childcare"]
        await _seed_session(test_engine, sid, barriers, tok)

        r = await client.post(
            f"/api/simulate?token={tok}",
            json={
                "session_id": sid,
                "resolved_barriers": ["criminal_record"],
            },
        )
        assert r.status_code == 200
        data = r.json()

        # Remaining should be 3 barriers
        assert len(data["barriers_remaining"]) == 3
        # sequence_after should have steps for remaining
        seq = data["sequence_after"]
        assert seq["total_barriers"] == 3
        step_ids = [s["barrier_id"] for s in seq["steps"]]
        assert "criminal_record" not in step_ids

    @pytest.mark.anyio
    async def test_simulate_with_unknown_barrier(self, client, test_engine):
        """Simulate handles unknown barrier types gracefully."""
        sid = "00000000-0000-4000-8000-a00000000002"
        tok = "sim-tok-2"
        barriers = ["criminal_record", "unknown_barrier"]
        await _seed_session(test_engine, sid, barriers, tok)

        r = await client.post(
            f"/api/simulate?token={tok}",
            json={
                "session_id": sid,
                "resolved_barriers": ["unknown_barrier"],
            },
        )
        assert r.status_code == 200
        data = r.json()
        assert "unknown_barrier" not in data["barriers_remaining"]
        # Unknown barrier defaults to 3 jobs
        assert data["jobs_unlocked_estimate"] == 3


# ---------------------------------------------------------------------------
# Sequence -> API: topological order with timeline
# ---------------------------------------------------------------------------

class TestSequenceAPI:
    """Sequence API returns correct topological order and timeline."""

    @pytest.mark.anyio
    async def test_sequence_returns_ordered_steps(self, client, test_engine):
        """Sequence endpoint returns deterministic ordered steps with timeline."""
        sid = "00000000-0000-4000-8000-b00000000001"
        tok = "seq-tok-1"
        barriers = ["credit", "criminal_record", "transportation"]
        await _seed_session(test_engine, sid, barriers, tok)

        r = await client.get(f"/api/plan/{sid}/sequence?token={tok}")
        assert r.status_code == 200
        data = r.json()
        assert data["total_barriers"] == 3
        assert len(data["steps"]) == 3

        # Each step should have timeline and valid fields
        for step in data["steps"]:
            assert step["estimated_weeks"] > 0
            assert step["barrier_name"] != ""
            assert step["order"] > 0

        # Ordering should be deterministic (alphabetical for same-level nodes)
        step_ids = [s["barrier_id"] for s in data["steps"]]
        assert len(set(step_ids)) == 3  # No duplicates

    @pytest.mark.anyio
    async def test_sequence_with_all_seven_types(self, client, test_engine):
        """Sequence handles all 7 barrier types."""
        sid = "00000000-0000-4000-8000-b00000000002"
        tok = "seq-tok-2"
        barriers = [
            "criminal_record", "credit", "transportation",
            "childcare", "housing", "health", "training",
        ]
        await _seed_session(test_engine, sid, barriers, tok)

        r = await client.get(f"/api/plan/{sid}/sequence?token={tok}")
        assert r.status_code == 200
        data = r.json()
        assert data["total_barriers"] == 7
        assert len(data["steps"]) == 7
        assert data["estimated_total_weeks"] > 0

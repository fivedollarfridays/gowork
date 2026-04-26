"""End-to-end integration tests for the full demo flow.

Tests the complete path: assessment -> plan -> sequence -> simulate -> share -> pathway
This is what a HackFW judge would exercise.
"""

import json
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text

from app.core.database import get_async_session_factory


def _build_test_plan(session_id: str, barriers: list[str]) -> str:
    """Build a JSON plan payload for integration tests."""
    return json.dumps({
        "plan_id": "int-test",
        "session_id": session_id,
        "barriers": [{"type": b} for b in barriers],
        "immediate_next_steps": [
            "Visit career center for intake",
            "Schedule credit counseling",
            "Apply for transit pass",
        ],
        "job_matches": [
            {"title": "Warehouse Associate", "url": "https://example.com/job1"},
            {"title": "Customer Service Rep", "url": "https://example.com/job2"},
        ],
    })


async def _seed_full_session(
    test_engine,
    session_id: str,
    barriers: list[str],
    *,
    auth_token: str,
    benefits_profile: dict | None = None,
) -> str:
    """Insert a fully-formed session with plan, barriers, and optional benefits."""
    factory = get_async_session_factory()
    async with factory() as db:
        now = datetime.now(timezone.utc)
        expires = (now + timedelta(days=30)).isoformat()
        plan = _build_test_plan(session_id, barriers)
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


class TestFullDemoFlow:
    """Full assessment -> plan -> sequence -> simulate -> share flow."""

    @pytest.mark.anyio
    async def test_plan_to_sequence_to_share(self, client, test_engine):
        """Complete flow: get plan -> get sequence -> share plan."""
        sid = "00000000-0000-4000-8000-f100e0000001"
        tok = await _seed_full_session(
            test_engine, sid,
            ["criminal_record", "credit", "transportation"],
            auth_token="flow-tok-1",
        )

        # Step 1: Get plan
        r1 = await client.get(f"/api/plan/{sid}?token={tok}")
        assert r1.status_code == 200
        plan_data = r1.json()
        assert plan_data["session_id"] == sid
        assert plan_data["plan"] is not None
        assert len(plan_data["barriers"]) == 3

        # Step 2: Get barrier sequence
        r2 = await client.get(f"/api/plan/{sid}/sequence?token={tok}")
        assert r2.status_code == 200
        seq_data = r2.json()
        assert seq_data["total_barriers"] == 3
        assert len(seq_data["steps"]) == 3

        # Step 3: Share the plan
        r3 = await client.post(f"/api/plan/{sid}/share?token={tok}")
        assert r3.status_code == 200
        share_token = r3.json()["share_token"]

        # Step 4: Retrieve shared plan (public, no auth) — payload is
        # redacted to strip session_id and raw barrier slugs (T13.71 P1).
        r4 = await client.get(f"/api/plan/shared/{share_token}")
        assert r4.status_code == 200
        shared = r4.json()
        assert "session_id" not in shared
        assert sid not in r4.text
        assert shared["barriers_count"] == 3
        assert len(shared["next_steps"]) > 0
        assert shared["career_center_name"] != ""

    @pytest.mark.anyio
    async def test_simulate_then_sequence(self, client, test_engine):
        """Simulate resolving barriers, then check new sequence."""
        sid = "00000000-0000-4000-8000-f100e0000002"
        tok = await _seed_full_session(
            test_engine, sid,
            ["criminal_record", "credit", "childcare"],
            auth_token="flow-tok-2",
        )

        # Simulate resolving criminal_record
        r1 = await client.post(
            f"/api/simulate?token={tok}",
            json={"session_id": sid, "resolved_barriers": ["criminal_record"]},
        )
        assert r1.status_code == 200
        sim = r1.json()
        assert "criminal_record" not in sim["barriers_remaining"]
        assert sim["jobs_unlocked_estimate"] > 0
        assert len(sim["benefits_unlocked"]) > 0

        # Verify sequence_after only has remaining barriers
        after_ids = {s["barrier_id"] for s in sim["sequence_after"]["steps"]}
        assert "criminal_record" not in after_ids

    @pytest.mark.anyio
    async def test_pathway_after_plan(self, client, test_engine):
        """Generate pathway after plan exists."""
        sid = "00000000-0000-4000-8000-f100e0000003"
        bp = {"household_size": 2, "annual_income": 20000, "enrolled_programs": ["snap"]}
        tok = await _seed_full_session(
            test_engine, sid,
            ["credit", "transportation"],
            auth_token="flow-tok-3",
            benefits_profile=bp,
        )

        # Get plan first
        r1 = await client.get(f"/api/plan/{sid}?token={tok}")
        assert r1.status_code == 200

        # Generate pathways
        r2 = await client.post(
            f"/api/pathway?token={tok}",
            json={"session_id": sid, "current_wage": 10.0},
        )
        assert r2.status_code == 200
        pathways = r2.json()
        assert "pathways" in pathways
        assert len(pathways["pathways"]) > 0

    @pytest.mark.anyio
    async def test_city_endpoint_accessible(self, client, test_engine):
        """City config endpoint is registered and returns data."""
        resp = await client.get("/api/city")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] in ("Montgomery", "Fort Worth")
        assert len(data["zip_ranges"]) > 0

    @pytest.mark.anyio
    async def test_health_endpoint(self, client, test_engine):
        """Health check is accessible."""
        resp = await client.get("/health")
        assert resp.status_code == 200

    @pytest.mark.anyio
    async def test_all_routes_registered(self, client, test_engine):
        """All expected API routes respond (not 404)."""
        # GET routes that should exist
        get_routes = [
            "/api/city",
            "/health",
            "/api/dashboard/stats",
            "/api/outcomes/aggregate",
        ]
        for route in get_routes:
            resp = await client.get(route)
            assert resp.status_code != 404, f"{route} returned 404 — not registered"

        # POST routes that require body (expect 422, not 404)
        post_routes = [
            "/api/simulate",
            "/api/pathway",
        ]
        for route in post_routes:
            resp = await client.post(route, json={})
            assert resp.status_code != 404, f"{route} returned 404 — not registered"

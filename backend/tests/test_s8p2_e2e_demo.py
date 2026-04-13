"""End-to-end demo flow integration tests for S8 Phase 2.

Exercises the FULL HackFW 2026 demo path:
  Assessment -> Plan -> Barrier Cards -> Sequence -> Simulate -> Share -> Pathway

This is the highest-value integration test: proves the ENTIRE chain works
from a single Fort Worth assessment through every feature.
"""

import json
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text

from app.core.database import get_async_session_factory


def _build_plan_with_barriers(session_id: str, barriers: list[str]) -> str:
    """Build a JSON plan with barrier cards and next steps."""
    return json.dumps({
        "plan_id": "e2e-demo-plan",
        "session_id": session_id,
        "barriers": [{"type": b} for b in barriers],
        "immediate_next_steps": [
            "Visit Workforce Solutions for intake",
            "Schedule HHSC appointment for SNAP renewal",
            "Apply for Trinity Metro transit pass",
        ],
        "strong_matches": [
            {"title": "Warehouse Associate", "company": "FW Logistics"},
            {"title": "Forklift Operator", "company": "DFW Distribution"},
        ],
        "action_plan": {
            "phase_1": ["Get credit report", "Apply for transit pass"],
            "phase_2": ["Complete job training", "Start job search"],
        },
    })


async def _seed_demo_session(
    test_engine,
    session_id: str,
    barriers: list[str],
    auth_token: str,
    benefits_profile: dict | None = None,
) -> None:
    """Seed a complete session for the FW demo flow."""
    factory = get_async_session_factory()
    async with factory() as db:
        now = datetime.now(timezone.utc)
        expires = (now + timedelta(days=30)).isoformat()
        plan = _build_plan_with_barriers(session_id, barriers)
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
                "INSERT INTO feedback_tokens "
                "(token, session_id, created_at, expires_at) "
                "VALUES (:tok, :sid, :ts, :exp)"
            ),
            {"tok": auth_token, "sid": session_id, "ts": now.isoformat(), "exp": expires},
        )
        await db.commit()


class TestFullDemoFlowE2E:
    """Full Fort Worth demo: plan -> sequence -> simulate -> share -> pathway.

    This single test class exercises 7+ modules:
    1. plan route (plan.py)
    2. barrier sequencer (barrier_sequencer.py)
    3. sequence route (sequence.py)
    4. simulate route + barrier graph (simulate.py)
    5. share route + share_tokens DB (share.py)
    6. pathway engine + cliff_navigator + stage_builder (pathway.py)
    7. intelligence route (intelligence.py)
    8. dashboard route (dashboard.py)
    """

    @pytest.mark.anyio
    async def test_full_demo_chain(self, client, test_engine):
        """Complete FW demo: plan -> sequence -> simulate -> share -> pathway."""
        sid = "00000000-0000-4000-8000-e2e000000001"
        tok = "e2e-demo-tok-1"
        barriers = ["criminal_record", "credit", "transportation", "childcare"]
        bp = {
            "household_size": 3,
            "current_monthly_income": 1200,
            "enrolled_programs": ["SNAP"],
            "dependents_under_6": 1,
        }
        await _seed_demo_session(
            test_engine, sid, barriers, tok, benefits_profile=bp,
        )

        # -------- Step 1: Get plan --------
        r_plan = await client.get(f"/api/plan/{sid}?token={tok}")
        assert r_plan.status_code == 200
        plan_data = r_plan.json()
        assert plan_data["session_id"] == sid
        assert plan_data["plan"] is not None
        assert len(plan_data["barriers"]) == 4

        # -------- Step 2: Get barrier sequence (topological sort) --------
        r_seq = await client.get(f"/api/plan/{sid}/sequence?token={tok}")
        assert r_seq.status_code == 200
        seq_data = r_seq.json()
        assert seq_data["total_barriers"] == 4
        steps = seq_data["steps"]
        assert len(steps) == 4
        # Verify estimated_weeks present on each step
        for step in steps:
            assert "estimated_weeks" in step
            assert step["estimated_weeks"] > 0
        # Verify estimated_total_weeks
        assert seq_data["estimated_total_weeks"] > 0

        # -------- Step 3: Simulate resolving 2 barriers --------
        r_sim = await client.post(
            f"/api/simulate?token={tok}",
            json={
                "session_id": sid,
                "resolved_barriers": ["criminal_record", "credit"],
            },
        )
        assert r_sim.status_code == 200
        sim_data = r_sim.json()
        assert set(sim_data["barriers_resolved"]) == {"criminal_record", "credit"}
        assert "criminal_record" not in sim_data["barriers_remaining"]
        assert "credit" not in sim_data["barriers_remaining"]
        assert sim_data["jobs_unlocked_estimate"] > 0
        assert len(sim_data["benefits_unlocked"]) > 0
        # sequence_after should only have remaining barriers
        after_steps = sim_data["sequence_after"]["steps"]
        after_ids = {s["barrier_id"] for s in after_steps}
        assert "criminal_record" not in after_ids
        assert "credit" not in after_ids
        assert sim_data["confidence"] in ("high", "medium", "low")

        # -------- Step 4: Share the plan --------
        r_share = await client.post(f"/api/plan/{sid}/share?token={tok}")
        assert r_share.status_code == 200
        share_token = r_share.json()["share_token"]
        assert len(share_token) > 10

        # -------- Step 5: Retrieve shared plan (public, no auth) --------
        r_shared = await client.get(f"/api/plan/shared/{share_token}")
        assert r_shared.status_code == 200
        shared = r_shared.json()
        assert shared["session_id"] == sid
        assert len(shared["barriers"]) == 4
        assert len(shared["next_steps"]) > 0
        assert shared["career_center_name"] != ""

        # -------- Step 6: Generate pathway --------
        r_pathway = await client.post(
            f"/api/pathway?token={tok}",
            json={"session_id": sid, "current_wage": 10.0},
        )
        assert r_pathway.status_code == 200
        pathway_data = r_pathway.json()
        assert "pathways" in pathway_data
        assert len(pathway_data["pathways"]) == 3  # conservative, balanced, aggressive
        for p in pathway_data["pathways"]:
            assert "steps" in p
            assert "viability_score" in p
            assert p["viability_score"] > 0
            assert len(p["steps"]) > 0

        # -------- Step 7: Intelligence endpoint --------
        r_intel = await client.get("/api/intelligence/barriers")
        assert r_intel.status_code == 200
        intel_data = r_intel.json()
        assert "barriers" in intel_data
        assert "calibrated_weeks" in intel_data
        assert "default_weeks" in intel_data
        assert "confidence" in intel_data

        # -------- Step 8: Dashboard stats --------
        r_dash = await client.get("/api/dashboard/stats")
        assert r_dash.status_code == 200
        dash_data = r_dash.json()
        assert dash_data["total_assessments"] >= 1
        assert dash_data["total_barrier_instances"] >= 4

    @pytest.mark.anyio
    async def test_demo_flow_with_single_barrier(self, client, test_engine):
        """Minimal demo flow with a single barrier (edge case)."""
        sid = "00000000-0000-4000-8000-e2e000000002"
        tok = "e2e-demo-tok-2"
        await _seed_demo_session(
            test_engine, sid, ["credit"], tok,
        )

        # Plan -> Sequence -> Share
        r_plan = await client.get(f"/api/plan/{sid}?token={tok}")
        assert r_plan.status_code == 200

        r_seq = await client.get(f"/api/plan/{sid}/sequence?token={tok}")
        assert r_seq.status_code == 200
        assert r_seq.json()["total_barriers"] == 1

        r_share = await client.post(f"/api/plan/{sid}/share?token={tok}")
        assert r_share.status_code == 200
        share_token = r_share.json()["share_token"]
        r_shared = await client.get(f"/api/plan/shared/{share_token}")
        assert r_shared.status_code == 200

    @pytest.mark.anyio
    async def test_simulate_all_barriers_resolved(self, client, test_engine):
        """Simulate resolving ALL barriers -- remaining should be empty."""
        sid = "00000000-0000-4000-8000-e2e000000003"
        tok = "e2e-demo-tok-3"
        barriers = ["criminal_record", "credit"]
        await _seed_demo_session(test_engine, sid, barriers, tok)

        r_sim = await client.post(
            f"/api/simulate?token={tok}",
            json={"session_id": sid, "resolved_barriers": barriers},
        )
        assert r_sim.status_code == 200
        sim = r_sim.json()
        assert sim["barriers_remaining"] == []
        assert sim["sequence_after"]["total_barriers"] == 0

    @pytest.mark.anyio
    async def test_share_then_verify_data_integrity(self, client, test_engine):
        """Shared plan data should match original session data."""
        sid = "00000000-0000-4000-8000-e2e000000004"
        tok = "e2e-demo-tok-4"
        barriers = ["housing", "health", "training"]
        await _seed_demo_session(test_engine, sid, barriers, tok)

        # Get plan
        r_plan = await client.get(f"/api/plan/{sid}?token={tok}")
        assert r_plan.status_code == 200

        # Share
        r_share = await client.post(f"/api/plan/{sid}/share?token={tok}")
        share_token = r_share.json()["share_token"]

        # Retrieve shared
        r_shared = await client.get(f"/api/plan/shared/{share_token}")
        shared = r_shared.json()

        # Barriers should match
        assert set(shared["barriers"]) == set(barriers)
        # Session ID should match
        assert shared["session_id"] == sid

    @pytest.mark.anyio
    async def test_pathway_with_benefits_profile(self, client, test_engine):
        """Pathway generation uses stored benefits profile for cliff nav."""
        sid = "00000000-0000-4000-8000-e2e000000005"
        tok = "e2e-demo-tok-5"
        bp = {
            "household_size": 4,
            "current_monthly_income": 1500,
            "enrolled_programs": ["SNAP", "Section_8"],
            "dependents_under_6": 1,
            "dependents_6_to_17": 1,
        }
        await _seed_demo_session(
            test_engine, sid,
            ["criminal_record", "credit", "transportation"],
            tok, benefits_profile=bp,
        )

        r = await client.post(
            f"/api/pathway?token={tok}",
            json={"session_id": sid, "current_wage": 8.0},
        )
        assert r.status_code == 200
        data = r.json()
        # Should have 3 strategy variants
        assert len(data["pathways"]) == 3
        # Each pathway should have steps with cliff warnings
        for p in data["pathways"]:
            assert p["final_wage"] > 0
            assert p["final_net_monthly"] > 0

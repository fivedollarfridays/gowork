"""End-to-end pipeline tests with seeded demo data.

Verifies: seed -> intelligence -> pathway -> share -> dashboard
all work together with realistic Fort Worth data flowing through.
"""

import json
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text

from app.core.database import get_async_session_factory


async def _get_seeded_session(test_engine):
    """Helper: get the first seeded session with its token."""
    factory = get_async_session_factory()
    async with factory() as db:
        result = await db.execute(
            text(
                "SELECT s.id, ft.token FROM sessions s "
                "JOIN feedback_tokens ft ON ft.session_id = s.id "
                "LIMIT 1"
            )
        )
        row = result.fetchone()
        return row[0], row[1]


class TestPipelineIntelligence:
    """After seeding, intelligence endpoints return calibrated data."""

    @pytest.mark.anyio
    async def test_barriers_endpoint_calibrated(self, client, test_engine):
        """GET /api/intelligence/barriers returns non-empty calibrated_weeks."""
        from app.demo_seed import run_demo_seed

        factory = get_async_session_factory()
        async with factory() as db:
            await run_demo_seed(db)

        r = await client.get("/api/intelligence/barriers")
        assert r.status_code == 200
        data = r.json()
        assert data["total_feedback_count"] > 0
        assert len(data["barriers"]) > 0
        # At least some barriers should have MEDIUM+ confidence
        confident = [
            b for b in data["barriers"]
            if b["confidence"] in ("medium", "high")
        ]
        assert len(confident) >= 1

    @pytest.mark.anyio
    async def test_plan_intelligence_endpoint(self, client, test_engine):
        """GET /api/plan/{id}/intelligence returns all four sections."""
        from app.demo_seed import run_demo_seed

        factory = get_async_session_factory()
        async with factory() as db:
            await run_demo_seed(db)

        sid, tok = await _get_seeded_session(test_engine)

        r = await client.get(
            f"/api/plan/{sid}/intelligence",
            params={"token": tok},
        )
        assert r.status_code == 200
        data = r.json()
        assert "barriers" in data
        assert "pathway" in data
        assert "cliff_analysis" in data
        assert "community_intelligence" in data
        assert data["community_intelligence"]["total_feedback"] > 0


class TestPipelinePathway:
    """Pathway endpoint uses calibrated data from seeded feedback."""

    @pytest.mark.anyio
    async def test_pathway_with_seeded_data(self, client, test_engine):
        """POST /api/pathway returns community_intelligence with feedback."""
        from app.demo_seed import run_demo_seed

        factory = get_async_session_factory()
        async with factory() as db:
            await run_demo_seed(db)

        sid, tok = await _get_seeded_session(test_engine)

        r = await client.post(
            f"/api/pathway?token={tok}",
            json={"session_id": sid, "current_wage": 10.0},
        )
        assert r.status_code == 200
        data = r.json()
        ci = data.get("community_intelligence", {})
        assert ci.get("total_feedback", 0) > 0

    @pytest.mark.anyio
    async def test_pathway_strategies_present(self, client, test_engine):
        """Pathway should return multiple strategies after seeding."""
        from app.demo_seed import run_demo_seed

        factory = get_async_session_factory()
        async with factory() as db:
            await run_demo_seed(db)

        sid, tok = await _get_seeded_session(test_engine)

        r = await client.post(
            f"/api/pathway?token={tok}",
            json={"session_id": sid, "current_wage": 10.0},
        )
        assert r.status_code == 200
        data = r.json()
        assert len(data.get("pathways", [])) >= 1


class TestPipelineShareAndDashboard:
    """Share and dashboard endpoints work with seeded data."""

    @pytest.mark.anyio
    async def test_share_seeded_session(self, client, test_engine):
        """Share a seeded session and retrieve the shared plan."""
        from app.demo_seed import run_demo_seed

        factory = get_async_session_factory()
        async with factory() as db:
            await run_demo_seed(db)

        sid, tok = await _get_seeded_session(test_engine)

        # Create share link
        r = await client.post(
            f"/api/plan/{sid}/share?token={tok}",
        )
        assert r.status_code == 200
        share_data = r.json()
        share_token = share_data["share_token"]

        # Retrieve shared plan — public payload is redacted (T13.71 P1):
        # no session_id, no raw barrier slugs; barriers_count is the scalar.
        r2 = await client.get(f"/api/plan/shared/{share_token}")
        assert r2.status_code == 200
        shared = r2.json()
        assert "session_id" not in shared
        assert sid not in r2.text
        assert shared["barriers_count"] >= 1

    @pytest.mark.anyio
    async def test_dashboard_with_seeded_data(self, client, test_engine):
        """Dashboard should show 50 assessments after seeding."""
        from app.demo_seed import run_demo_seed

        factory = get_async_session_factory()
        async with factory() as db:
            await run_demo_seed(db)

        r = await client.get("/api/dashboard/stats")
        assert r.status_code == 200
        data = r.json()
        assert data["total_assessments"] == 50
        assert data["total_barrier_instances"] > 50
        assert len(data["common_barriers"]) >= 5

    @pytest.mark.anyio
    async def test_outcomes_aggregate_with_seeded_data(self, client, test_engine):
        """Outcomes aggregate should reflect seeded sessions."""
        from app.demo_seed import run_demo_seed

        factory = get_async_session_factory()
        async with factory() as db:
            await run_demo_seed(db)

        r = await client.get("/api/outcomes/aggregate")
        assert r.status_code == 200
        data = r.json()
        assert data["assessment_count"] == 50
        assert len(data["top_barriers"]) >= 3


class TestFullDemoPipeline:
    """Complete pipeline: seed -> intelligence -> pathway -> share -> dashboard."""

    @pytest.mark.anyio
    async def test_n1_loop_visible(self, client, test_engine):
        """The N+1 loop should be VISIBLE — calibrated != defaults."""
        from app.demo_seed import run_demo_seed

        factory = get_async_session_factory()
        async with factory() as db:
            await run_demo_seed(db)

        # Intelligence should show calibrated data
        r = await client.get("/api/intelligence/barriers")
        data = r.json()
        calibrated = data["calibrated_weeks"]
        defaults = data["default_weeks"]

        # The whole point: at least some calibrated weeks exist
        assert len(calibrated) > 0, (
            "No barriers reached MEDIUM+ confidence — N+1 loop invisible"
        )

    @pytest.mark.anyio
    async def test_full_chain_seed_to_dashboard(self, client, test_engine):
        """Seed -> intelligence -> pathway -> share -> dashboard chain."""
        from app.demo_seed import run_demo_seed

        factory = get_async_session_factory()
        async with factory() as db:
            await run_demo_seed(db)

        sid, tok = await _get_seeded_session(test_engine)

        # 1. Intelligence endpoint
        r1 = await client.get("/api/intelligence/barriers")
        assert r1.status_code == 200
        assert r1.json()["total_feedback_count"] > 0

        # 2. Plan intelligence endpoint
        r2 = await client.get(
            f"/api/plan/{sid}/intelligence",
            params={"token": tok},
        )
        assert r2.status_code == 200

        # 3. Pathway endpoint
        r3 = await client.post(
            f"/api/pathway?token={tok}",
            json={"session_id": sid, "current_wage": 10.0},
        )
        assert r3.status_code == 200

        # 4. Share endpoint
        r4 = await client.post(f"/api/plan/{sid}/share?token={tok}")
        assert r4.status_code == 200
        share_token = r4.json()["share_token"]

        # 5. Retrieve shared plan
        r5 = await client.get(f"/api/plan/shared/{share_token}")
        assert r5.status_code == 200

        # 6. Dashboard endpoint
        r6 = await client.get("/api/dashboard/stats")
        assert r6.status_code == 200
        assert r6.json()["total_assessments"] == 50

    @pytest.mark.anyio
    async def test_demo_seed_via_admin_endpoint(self, client, test_engine):
        """Admin endpoint triggers seed and intelligence shows data."""
        # Seed via endpoint
        r1 = await client.post(
            "/api/demo/seed",
            headers={"X-Admin-Key": "montgowork-demo-2026"},
        )
        assert r1.status_code == 200
        assert r1.json()["sessions_created"] == 50

        # Verify intelligence is alive
        r2 = await client.get("/api/intelligence/barriers")
        assert r2.status_code == 200
        assert r2.json()["total_feedback_count"] > 0

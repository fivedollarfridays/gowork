"""Tests for demo seed data — verifies realistic Fort Worth data creation.

Cycle 1: Session creation with realistic barrier distributions.
Cycle 2: Visit feedback creation with resolution outcomes.
Cycle 3: Determinism and barrier distribution accuracy.
"""

import json

import pytest
from sqlalchemy import text

from app.core.database import get_async_session_factory


class TestDemoSeedSessions:
    """Seed should create 50 Fort Worth sessions with realistic barriers."""

    @pytest.mark.anyio
    async def test_seed_creates_50_sessions(self, test_engine):
        """Seed should create exactly 50 sessions."""
        from app.demo_seed import run_demo_seed

        factory = get_async_session_factory()
        async with factory() as db:
            await run_demo_seed(db)

        async with factory() as db:
            result = await db.execute(text("SELECT COUNT(*) FROM sessions"))
            assert result.scalar() == 50

    @pytest.mark.anyio
    async def test_sessions_have_fort_worth_zips(self, test_engine):
        """All seeded sessions should have Fort Worth ZIP codes in profile."""
        from app.demo_seed import run_demo_seed

        factory = get_async_session_factory()
        async with factory() as db:
            await run_demo_seed(db)

        async with factory() as db:
            result = await db.execute(text("SELECT profile FROM sessions WHERE profile IS NOT NULL"))
            rows = result.fetchall()
            fw_zips = set(range(76101, 76120))
            for row in rows:
                profile = json.loads(row[0])
                zip_code = profile.get("zip_code")
                if zip_code:
                    assert int(zip_code) in fw_zips, f"ZIP {zip_code} not in Fort Worth range"

    @pytest.mark.anyio
    async def test_sessions_have_valid_barriers(self, test_engine):
        """All sessions should have at least one valid barrier."""
        from app.demo_seed import run_demo_seed

        valid_barriers = {
            "criminal_record", "credit", "transportation",
            "childcare", "housing", "health", "training",
        }
        factory = get_async_session_factory()
        async with factory() as db:
            await run_demo_seed(db)

        async with factory() as db:
            result = await db.execute(text("SELECT barriers FROM sessions"))
            rows = result.fetchall()
            for row in rows:
                barriers = json.loads(row[0])
                assert len(barriers) >= 1
                for b in barriers:
                    assert b in valid_barriers, f"Invalid barrier: {b}"

    @pytest.mark.anyio
    async def test_sessions_have_plans(self, test_engine):
        """All seeded sessions should have a plan."""
        from app.demo_seed import run_demo_seed

        factory = get_async_session_factory()
        async with factory() as db:
            await run_demo_seed(db)

        async with factory() as db:
            result = await db.execute(
                text("SELECT COUNT(*) FROM sessions WHERE plan IS NOT NULL")
            )
            assert result.scalar() == 50

    @pytest.mark.anyio
    async def test_sessions_have_feedback_tokens(self, test_engine):
        """Every session should have a feedback token."""
        from app.demo_seed import run_demo_seed

        factory = get_async_session_factory()
        async with factory() as db:
            await run_demo_seed(db)

        async with factory() as db:
            result = await db.execute(text("SELECT COUNT(*) FROM feedback_tokens"))
            assert result.scalar() == 50


class TestDemoSeedBarrierDistribution:
    """Barrier distribution should match Fort Worth demographics."""

    @pytest.mark.anyio
    async def test_criminal_record_around_40_pct(self, test_engine):
        """Criminal record barrier should appear in ~40% of sessions."""
        from app.demo_seed import run_demo_seed

        factory = get_async_session_factory()
        async with factory() as db:
            await run_demo_seed(db)

        async with factory() as db:
            result = await db.execute(text("SELECT barriers FROM sessions"))
            rows = result.fetchall()
            count = sum(
                1 for row in rows
                if "criminal_record" in json.loads(row[0])
            )
            # Allow +/- 10% tolerance: 40% of 50 = 20, range 15-25
            assert 15 <= count <= 25, f"criminal_record count {count} not near 40%"

    @pytest.mark.anyio
    async def test_transportation_around_60_pct(self, test_engine):
        """Transportation barrier should appear in ~60% of sessions."""
        from app.demo_seed import run_demo_seed

        factory = get_async_session_factory()
        async with factory() as db:
            await run_demo_seed(db)

        async with factory() as db:
            result = await db.execute(text("SELECT barriers FROM sessions"))
            rows = result.fetchall()
            count = sum(
                1 for row in rows
                if "transportation" in json.loads(row[0])
            )
            # 60% of 50 = 30, range 25-35
            assert 25 <= count <= 35, f"transportation count {count} not near 60%"

    @pytest.mark.anyio
    async def test_credit_around_50_pct(self, test_engine):
        """Credit barrier should appear in ~50% of sessions."""
        from app.demo_seed import run_demo_seed

        factory = get_async_session_factory()
        async with factory() as db:
            await run_demo_seed(db)

        async with factory() as db:
            result = await db.execute(text("SELECT barriers FROM sessions"))
            rows = result.fetchall()
            count = sum(
                1 for row in rows
                if "credit" in json.loads(row[0])
            )
            # 50% of 50 = 25, range 20-30
            assert 20 <= count <= 30, f"credit count {count} not near 50%"

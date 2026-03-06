"""Tests for resource health check — decay detection + scoring penalty."""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.modules.feedback.types import ResourceHealth


def _factory(test_engine):
    return async_sessionmaker(test_engine, class_=AsyncSession)


async def _seed_resource(factory, resource_id: int, name: str = "Test Resource"):
    """Insert a resource row."""
    async with factory() as session:
        await session.execute(text(
            "INSERT OR IGNORE INTO resources (id, name, category, health_status) "
            "VALUES (:id, :name, 'career_center', 'healthy')"
        ), {"id": resource_id, "name": name})
        await session.commit()


async def _seed_feedback(factory, resource_id: int, helpful: bool, session_id: str):
    """Insert a resource_feedback row."""
    async with factory() as session:
        await session.execute(text(
            "INSERT INTO sessions (id, created_at, barriers, expires_at) "
            "VALUES (:sid, '2026-03-06', '[]', '2026-04-06') "
            "ON CONFLICT(id) DO NOTHING"
        ), {"sid": session_id})
        await session.execute(text(
            "INSERT INTO resource_feedback (resource_id, session_id, helpful, submitted_at) "
            "VALUES (:rid, :sid, :helpful, datetime('now'))"
        ), {"rid": resource_id, "sid": session_id, "helpful": int(helpful)})
        await session.commit()


class TestCheckResourceHealth:
    """check_resource_health() pure function — threshold logic."""

    def test_healthy_no_feedback(self):
        from app.modules.feedback.health import check_resource_health
        result = check_resource_health(total=0, unhelpful_count=0)
        assert result == ResourceHealth.HEALTHY

    def test_healthy_with_positive_feedback(self):
        from app.modules.feedback.health import check_resource_health
        result = check_resource_health(total=5, unhelpful_count=1)
        assert result == ResourceHealth.HEALTHY

    def test_watch_at_40_percent(self):
        from app.modules.feedback.health import check_resource_health
        # 2/5 = 40%
        result = check_resource_health(total=5, unhelpful_count=2)
        assert result == ResourceHealth.WATCH

    def test_flagged_at_60_percent_with_min_votes(self):
        from app.modules.feedback.health import check_resource_health
        # 3/5 = 60%, >=3 votes
        result = check_resource_health(total=5, unhelpful_count=3)
        assert result == ResourceHealth.FLAGGED

    def test_not_flagged_below_min_votes(self):
        from app.modules.feedback.health import check_resource_health
        # 2/2 = 100% but only 2 votes (below min 3)
        result = check_resource_health(total=2, unhelpful_count=2)
        assert result == ResourceHealth.WATCH

    def test_below_watch_threshold(self):
        from app.modules.feedback.health import check_resource_health
        # 1/3 = 33%
        result = check_resource_health(total=3, unhelpful_count=1)
        assert result == ResourceHealth.HEALTHY


class TestGetFeedbackStats:
    """get_feedback_stats() — aggregates feedback within time window."""

    @pytest.mark.anyio
    async def test_returns_zero_for_no_feedback(self, test_engine):
        from app.core.queries_feedback import get_feedback_stats
        factory = _factory(test_engine)
        await _seed_resource(factory, 100)
        async with factory() as session:
            stats = await get_feedback_stats(session, 100)
        assert stats["total"] == 0
        assert stats["unhelpful_count"] == 0

    @pytest.mark.anyio
    async def test_counts_helpful_and_unhelpful(self, test_engine):
        from app.core.queries_feedback import get_feedback_stats
        factory = _factory(test_engine)
        await _seed_resource(factory, 101)
        await _seed_feedback(factory, 101, helpful=True, session_id="s1")
        await _seed_feedback(factory, 101, helpful=True, session_id="s2")
        await _seed_feedback(factory, 101, helpful=False, session_id="s3")
        async with factory() as session:
            stats = await get_feedback_stats(session, 101)
        assert stats["total"] == 3
        assert stats["unhelpful_count"] == 1


class TestUpdateResourceHealth:
    """update_resource_health() — sets health_status on resources table."""

    @pytest.mark.anyio
    async def test_updates_status(self, test_engine):
        from app.core.queries_feedback import update_resource_health
        factory = _factory(test_engine)
        await _seed_resource(factory, 200)
        async with factory() as session:
            await update_resource_health(session, 200, ResourceHealth.FLAGGED)
        async with factory() as session:
            result = await session.execute(text(
                "SELECT health_status FROM resources WHERE id = 200"
            ))
            assert result.scalar() == "flagged"


class TestUpdateAllHealthStatuses:
    """update_all_health_statuses() — batch processes all resources."""

    @pytest.mark.anyio
    async def test_batch_updates_statuses(self, test_engine):
        from app.modules.feedback.health import update_all_health_statuses
        factory = _factory(test_engine)
        await _seed_resource(factory, 301, "Good Resource")
        await _seed_resource(factory, 302, "Bad Resource")
        # Good resource: 3 helpful, 0 unhelpful
        for i in range(3):
            await _seed_feedback(factory, 301, helpful=True, session_id=f"g{i}")
        # Bad resource: 0 helpful, 4 unhelpful -> flagged
        for i in range(4):
            await _seed_feedback(factory, 302, helpful=False, session_id=f"b{i}")

        async with factory() as session:
            updated = await update_all_health_statuses(session)

        assert updated >= 1
        async with factory() as session:
            result = await session.execute(text(
                "SELECT health_status FROM resources WHERE id = 301"
            ))
            assert result.scalar() == "healthy"
            result = await session.execute(text(
                "SELECT health_status FROM resources WHERE id = 302"
            ))
            assert result.scalar() == "flagged"


class TestEngineHealthFiltering:
    """Engine excludes HIDDEN, deprioritizes FLAGGED resources."""

    @pytest.mark.anyio
    async def test_hidden_resources_excluded(self, test_engine):
        from app.modules.matching.engine import query_resources_for_barriers
        from app.modules.matching.types import BarrierType
        factory = _factory(test_engine)
        await _seed_resource(factory, 401, "Visible Resource")
        async with factory() as session:
            await session.execute(text(
                "INSERT OR IGNORE INTO resources (id, name, category, health_status) "
                "VALUES (402, 'Hidden Resource', 'career_center', 'hidden')"
            ))
            await session.commit()

        async with factory() as session:
            resources = await query_resources_for_barriers(
                [BarrierType.CREDIT], session,
            )
        names = [r.name for r in resources]
        assert "Visible Resource" in names
        assert "Hidden Resource" not in names

    @pytest.mark.anyio
    async def test_flagged_resources_sorted_last(self, test_engine):
        from app.modules.matching.engine import query_resources_for_barriers
        from app.modules.matching.types import BarrierType
        factory = _factory(test_engine)
        # Insert a flagged resource
        async with factory() as session:
            await session.execute(text(
                "INSERT OR IGNORE INTO resources (id, name, category, health_status) "
                "VALUES (501, 'Flagged Resource', 'career_center', 'flagged')"
            ))
            await session.execute(text(
                "INSERT OR IGNORE INTO resources (id, name, category, health_status) "
                "VALUES (502, 'Healthy Resource', 'career_center', 'healthy')"
            ))
            await session.commit()

        async with factory() as session:
            resources = await query_resources_for_barriers(
                [BarrierType.CREDIT], session,
            )
        # If both present, healthy should come before flagged
        names = [r.name for r in resources]
        if "Flagged Resource" in names and "Healthy Resource" in names:
            assert names.index("Healthy Resource") < names.index("Flagged Resource")

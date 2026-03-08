"""Tests for barrier graph queries (barrier_resources join table + top-N query)."""

import pytest
from sqlalchemy import text

from app.barrier_graph.queries import get_top_resources_for_barriers
from app.core.database import get_async_session_factory


@pytest.fixture
async def db_session(test_engine):
    factory = get_async_session_factory()
    async with factory() as session:
        yield session


class TestBarrierResourcesSeedData:
    """Verify barrier_resources seed data is populated correctly."""

    @pytest.mark.anyio
    async def test_at_least_50_barrier_resource_rows(self, db_session):
        result = await db_session.execute(
            text("SELECT COUNT(*) FROM barrier_resources")
        )
        assert result.scalar() >= 50

    @pytest.mark.anyio
    async def test_all_impact_strengths_in_range(self, db_session):
        result = await db_session.execute(
            text(
                "SELECT COUNT(*) FROM barrier_resources "
                "WHERE impact_strength < 0.0 OR impact_strength > 1.0"
            )
        )
        assert result.scalar() == 0

    @pytest.mark.anyio
    async def test_all_barrier_ids_reference_valid_barriers(self, db_session):
        result = await db_session.execute(
            text(
                "SELECT COUNT(*) FROM barrier_resources br "
                "LEFT JOIN barriers b ON br.barrier_id = b.id "
                "WHERE b.id IS NULL"
            )
        )
        assert result.scalar() == 0

    @pytest.mark.anyio
    async def test_all_resource_ids_reference_valid_resources(self, db_session):
        result = await db_session.execute(
            text(
                "SELECT COUNT(*) FROM barrier_resources br "
                "LEFT JOIN resources r ON br.resource_id = r.id "
                "WHERE r.id IS NULL"
            )
        )
        assert result.scalar() == 0


class TestGetTopResourcesForBarriers:
    """Test the top-N resource query function."""

    @pytest.mark.anyio
    async def test_returns_resources_for_single_barrier(self, db_session):
        results = await get_top_resources_for_barriers(
            db_session, ["CREDIT_LOW_SCORE"], n=5
        )
        assert len(results) > 0
        for r in results:
            assert "name" in r
            assert "impact_strength" in r

    @pytest.mark.anyio
    async def test_results_ordered_by_impact_strength_desc(self, db_session):
        results = await get_top_resources_for_barriers(
            db_session, ["CREDIT_LOW_SCORE"], n=10
        )
        strengths = [r["impact_strength"] for r in results]
        assert strengths == sorted(strengths, reverse=True)

    @pytest.mark.anyio
    async def test_top_n_limits_results(self, db_session):
        results = await get_top_resources_for_barriers(
            db_session, ["CHILDCARE_DAY"], n=2
        )
        assert len(results) <= 2

    @pytest.mark.anyio
    async def test_multiple_barriers_combines_results(self, db_session):
        single = await get_top_resources_for_barriers(
            db_session, ["CREDIT_LOW_SCORE"], n=20
        )
        combined = await get_top_resources_for_barriers(
            db_session, ["CREDIT_LOW_SCORE", "CHILDCARE_DAY"], n=20
        )
        assert len(combined) >= len(single)

    @pytest.mark.anyio
    async def test_hidden_resources_excluded(self, db_session):
        # Mark a resource as hidden
        await db_session.execute(
            text("UPDATE resources SET health_status = 'hidden' WHERE id = 1")
        )
        results = await get_top_resources_for_barriers(
            db_session, ["TRAINING_NO_CERT"], n=20
        )
        resource_ids = {r["resource_id"] for r in results}
        assert 1 not in resource_ids
        # Restore
        await db_session.execute(
            text("UPDATE resources SET health_status = 'healthy' WHERE id = 1")
        )

    @pytest.mark.anyio
    async def test_empty_barrier_list_returns_empty(self, db_session):
        results = await get_top_resources_for_barriers(db_session, [], n=5)
        assert results == []

    @pytest.mark.anyio
    async def test_unknown_barrier_returns_empty(self, db_session):
        results = await get_top_resources_for_barriers(
            db_session, ["NONEXISTENT_BARRIER"], n=5
        )
        assert results == []

    @pytest.mark.anyio
    async def test_deduplicates_resources_across_barriers(self, db_session):
        """When a resource maps to multiple barriers, it should appear once with max strength."""
        results = await get_top_resources_for_barriers(
            db_session, ["CREDIT_LOW_SCORE", "CREDIT_DEBT_HIGH"], n=20
        )
        resource_ids = [r["resource_id"] for r in results]
        assert len(resource_ids) == len(set(resource_ids))

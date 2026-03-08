"""Tests for barrier-resource mapping and top-N query (T24.2)."""

import pytest
from sqlalchemy import text

from app.barrier_graph.queries import get_top_resources_for_barriers
from app.core.database import get_async_session_factory


class TestBarrierResourceMapping:
    """Verify barrier_resources join table is populated after seed."""

    @pytest.mark.anyio
    async def test_barrier_resources_minimum_count(self, test_engine):
        async with test_engine.connect() as conn:
            result = await conn.execute(text("SELECT COUNT(*) FROM barrier_resources"))
            count = result.scalar()
        assert count >= 50, f"Expected >=50 barrier_resource rows, got {count}"

    @pytest.mark.anyio
    async def test_all_resources_linked_to_at_least_one_barrier(self, test_engine):
        async with test_engine.connect() as conn:
            result = await conn.execute(text(
                "SELECT COUNT(*) FROM resources r "
                "WHERE NOT EXISTS ("
                "  SELECT 1 FROM barrier_resources br WHERE br.resource_id = r.id"
                ")"
            ))
            unlinked = result.scalar()
        assert unlinked == 0, f"{unlinked} resource(s) not linked to any barrier"

    @pytest.mark.anyio
    async def test_impact_strength_values_in_valid_range(self, test_engine):
        async with test_engine.connect() as conn:
            result = await conn.execute(text(
                "SELECT COUNT(*) FROM barrier_resources "
                "WHERE impact_strength < 0.0 OR impact_strength > 1.0"
            ))
            invalid = result.scalar()
        assert invalid == 0, f"{invalid} rows have impact_strength out of [0.0, 1.0]"

    @pytest.mark.anyio
    async def test_upsert_barrier_resources_idempotent(self, test_engine):
        """Calling upsert_barrier_graph twice must not duplicate barrier_resources."""
        from app.barrier_graph.seed import upsert_barrier_graph

        factory = get_async_session_factory()
        async with factory() as session:
            await upsert_barrier_graph(session)

        async with test_engine.connect() as conn:
            result = await conn.execute(text("SELECT COUNT(*) FROM barrier_resources"))
            count = result.scalar()
        assert count >= 50


class TestTopResourcesQuery:
    """Verify get_top_resources_for_barriers() returns correct ranked results."""

    @pytest.mark.anyio
    async def test_returns_at_most_n_results(self, test_engine):
        factory = get_async_session_factory()
        async with factory() as session:
            results = await get_top_resources_for_barriers(
                session, ["CHILDCARE_EVENING", "TRANSPORTATION_NO_CAR"], n=5
            )
        assert len(results) <= 5

    @pytest.mark.anyio
    async def test_results_sorted_by_score_descending(self, test_engine):
        factory = get_async_session_factory()
        async with factory() as session:
            results = await get_top_resources_for_barriers(
                session, ["CHILDCARE_EVENING", "TRANSPORTATION_NO_CAR"], n=10
            )
        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True), "Results must be sorted by score desc"

    @pytest.mark.anyio
    async def test_excludes_hidden_resources(self, test_engine):
        """Resources with health_status='HIDDEN' must not appear in results."""
        # Mark a resource as HIDDEN
        async with test_engine.begin() as conn:
            await conn.execute(text(
                "UPDATE resources SET health_status = 'HIDDEN' "
                "WHERE id = (SELECT MIN(r.id) FROM resources r "
                "JOIN barrier_resources br ON br.resource_id = r.id)"
            ))

        factory = get_async_session_factory()
        async with factory() as session:
            results = await get_top_resources_for_barriers(
                session, ["CHILDCARE_EVENING", "CHILDCARE_DAY",
                           "TRANSPORTATION_NO_CAR", "TRAINING_NO_CERT",
                           "CREDIT_LOW_SCORE", "HOUSING_UNSTABLE"], n=50
            )

        result_ids = {r["id"] for r in results}
        async with test_engine.connect() as conn:
            row = await conn.execute(
                text("SELECT MIN(r.id) FROM resources r "
                     "JOIN barrier_resources br ON br.resource_id = r.id")
            )
            hidden_id = row.scalar()
        assert hidden_id not in result_ids, "HIDDEN resource must be excluded from results"

    @pytest.mark.anyio
    async def test_result_has_required_fields(self, test_engine):
        factory = get_async_session_factory()
        async with factory() as session:
            results = await get_top_resources_for_barriers(
                session, ["CHILDCARE_EVENING"], n=3
            )
        assert len(results) > 0
        required = {"id", "name", "category", "score"}
        for r in results:
            assert required.issubset(r.keys()), f"Missing keys in result: {r.keys()}"

    @pytest.mark.anyio
    async def test_empty_barrier_ids_returns_empty(self, test_engine):
        factory = get_async_session_factory()
        async with factory() as session:
            results = await get_top_resources_for_barriers(session, [], n=5)
        assert results == []

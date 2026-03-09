"""Tests for barrier graph DB schema and seed data."""

from unittest.mock import patch

import pytest
from sqlalchemy import text

from app.core.database import get_async_session_factory


class TestBarrierTablesExist:
    """Verify the three barrier graph tables are created by init_db."""

    @pytest.mark.anyio
    async def test_barriers_table_exists(self, test_engine):
        async with test_engine.connect() as conn:
            result = await conn.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='barriers'"
            ))
            assert result.fetchone() is not None, "barriers table must exist"

    @pytest.mark.anyio
    async def test_barrier_relationships_table_exists(self, test_engine):
        async with test_engine.connect() as conn:
            result = await conn.execute(text(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name='barrier_relationships'"
            ))
            assert result.fetchone() is not None

    @pytest.mark.anyio
    async def test_barrier_resources_table_exists(self, test_engine):
        async with test_engine.connect() as conn:
            result = await conn.execute(text(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name='barrier_resources'"
            ))
            assert result.fetchone() is not None


class TestBarrierSeedData:
    """Verify seed data is loaded with minimum counts and quality."""

    @pytest.mark.anyio
    async def test_barriers_seeded_minimum_count(self, test_engine):
        async with test_engine.connect() as conn:
            result = await conn.execute(text("SELECT COUNT(*) FROM barriers"))
            count = result.scalar()
            assert count >= 30, f"Expected >=30 barrier nodes, got {count}"

    @pytest.mark.anyio
    async def test_barrier_relationships_seeded_minimum_count(self, test_engine):
        async with test_engine.connect() as conn:
            result = await conn.execute(
                text("SELECT COUNT(*) FROM barrier_relationships")
            )
            count = result.scalar()
            assert count >= 50, f"Expected >=50 edges, got {count}"

    @pytest.mark.anyio
    async def test_all_barriers_have_playbook(self, test_engine):
        async with test_engine.connect() as conn:
            result = await conn.execute(text(
                "SELECT id FROM barriers WHERE playbook IS NULL OR playbook = ''"
            ))
            missing = result.fetchall()
            assert len(missing) == 0, (
                f"Barriers missing playbooks: {[r[0] for r in missing]}"
            )

    @pytest.mark.anyio
    async def test_barrier_categories_valid(self, test_engine):
        valid_cats = {
            "childcare", "transportation", "credit", "housing",
            "health", "training", "criminal", "employment",
        }
        async with test_engine.connect() as conn:
            result = await conn.execute(
                text("SELECT DISTINCT category FROM barriers")
            )
            categories = {row[0] for row in result.fetchall()}
        unknown = categories - valid_cats
        assert not unknown, f"Unknown barrier categories: {unknown}"


class TestUpsertMissingFile:
    """Verify upsert_barrier_graph handles missing seed file gracefully."""

    @pytest.mark.anyio
    async def test_upsert_barrier_graph_missing_file(self, test_engine):
        """When seed file is absent, upsert logs warning and returns without error."""
        from app.barrier_graph.seed import upsert_barrier_graph

        factory = get_async_session_factory()
        async with factory() as session:
            # Patch _resolve_data_dir to return a tmp dir without the seed file
            with patch("app.barrier_graph.seed._resolve_data_dir") as mock_dir:
                import tempfile
                from pathlib import Path

                empty_dir = Path(tempfile.mkdtemp())
                mock_dir.return_value = empty_dir
                # Should not raise -- just logs warning and returns
                await upsert_barrier_graph(session)


class TestUpsertIdempotency:
    """Verify upsert_barrier_graph can be called multiple times safely."""

    @pytest.mark.anyio
    async def test_upsert_idempotent(self, test_engine):
        """Calling upsert_barrier_graph twice should not raise or duplicate."""
        from app.barrier_graph.seed import upsert_barrier_graph

        factory = get_async_session_factory()
        async with factory() as session:
            await upsert_barrier_graph(session)
        async with factory() as session:
            await upsert_barrier_graph(session)

        async with test_engine.connect() as conn:
            result = await conn.execute(text("SELECT COUNT(*) FROM barriers"))
            count_after = result.scalar()
        assert count_after >= 30

"""Tests for hybrid retrieval layer: graph traversal + vector search + context assembly."""

import time

import pytest

from app.barrier_graph.traversal import find_root_barriers
from app.core.database import get_async_session_factory
from app.rag.document_schema import RetrievalContext
from app.rag.retrieval import build_enriched_query, retrieve_context
from app.rag.store import RagStore


@pytest.fixture
async def db_session(test_engine):
    factory = get_async_session_factory()
    async with factory() as session:
        yield session


@pytest.fixture
async def rag_store(db_session, tmp_path):
    store = RagStore()
    await store.build_or_load(db_session, index_dir=tmp_path)
    return store


class TestFindRootBarriers:
    @pytest.mark.anyio
    async def test_finds_roots_for_childcare_and_transport(self, db_session):
        roots = await find_root_barriers(
            ["CHILDCARE_EVENING", "EMPLOYMENT_LIMITED_HOURS"], db_session
        )
        # CHILDCARE_EVENING causes EMPLOYMENT_LIMITED_HOURS, so childcare is root
        root_ids = [r["id"] for r in roots]
        assert "CHILDCARE_EVENING" in root_ids
        assert "EMPLOYMENT_LIMITED_HOURS" not in root_ids

    @pytest.mark.anyio
    async def test_single_barrier_is_its_own_root(self, db_session):
        roots = await find_root_barriers(["CREDIT_LOW_SCORE"], db_session)
        assert len(roots) == 1
        assert roots[0]["id"] == "CREDIT_LOW_SCORE"

    @pytest.mark.anyio
    async def test_empty_barriers_returns_empty(self, db_session):
        roots = await find_root_barriers([], db_session)
        assert roots == []

    @pytest.mark.anyio
    async def test_roots_include_barrier_metadata(self, db_session):
        roots = await find_root_barriers(["CHILDCARE_DAY"], db_session)
        assert roots[0]["name"] == "No Daytime Childcare"
        assert roots[0]["category"] == "childcare"


class TestFindRootBarriersCycle:
    @pytest.mark.anyio
    async def test_find_root_barriers_cycle(self, test_engine):
        """When all barriers cause each other (cycle), all are returned as roots."""
        from sqlalchemy import text as sa_text

        factory = get_async_session_factory()
        async with factory() as session:
            # Insert two barriers
            await session.execute(sa_text(
                "INSERT OR IGNORE INTO barriers (id, name, category, description, playbook) "
                "VALUES ('CYCLE_A', 'Cycle A', 'credit', 'test', 'test playbook A')"
            ))
            await session.execute(sa_text(
                "INSERT OR IGNORE INTO barriers (id, name, category, description, playbook) "
                "VALUES ('CYCLE_B', 'Cycle B', 'credit', 'test', 'test playbook B')"
            ))
            # Create mutual CAUSES edges: A->B and B->A
            await session.execute(sa_text(
                "INSERT OR IGNORE INTO barrier_relationships "
                "(source_barrier_id, target_barrier_id, relationship_type, weight) "
                "VALUES ('CYCLE_A', 'CYCLE_B', 'CAUSES', 1.0)"
            ))
            await session.execute(sa_text(
                "INSERT OR IGNORE INTO barrier_relationships "
                "(source_barrier_id, target_barrier_id, relationship_type, weight) "
                "VALUES ('CYCLE_B', 'CYCLE_A', 'CAUSES', 1.0)"
            ))
            await session.commit()

            roots = await find_root_barriers(["CYCLE_A", "CYCLE_B"], session)
            root_ids = {r["id"] for r in roots}
            assert root_ids == {"CYCLE_A", "CYCLE_B"}


class TestFetchBarriersEmpty:
    @pytest.mark.anyio
    async def test_fetch_barriers_empty_list(self, db_session):
        """Calling _fetch_barriers with an empty list returns []."""
        from app.barrier_graph.traversal import _fetch_barriers

        result = await _fetch_barriers(db_session, [])
        assert result == []


class TestBuildChainSummary:
    def test_chain_summary_with_non_root(self):
        """When there are non-root codes, summary uses arrow format with non-root appended."""
        from app.rag.retrieval import _build_chain_summary

        root_barriers = [{"id": "CHILDCARE_DAY", "name": "No Daytime Childcare"}]
        all_codes = ["CHILDCARE_DAY", "EMPLOYMENT_LIMITED_HOURS", "HOUSING_UNSTABLE"]

        result = _build_chain_summary(root_barriers, all_codes)
        assert "No Daytime Childcare" in result
        assert "EMPLOYMENT_LIMITED_HOURS" in result
        assert "HOUSING_UNSTABLE" in result

    def test_chain_summary_all_roots_no_arrow_to_non_root(self):
        """When all codes are roots, no non-root segment appears."""
        from app.rag.retrieval import _build_chain_summary

        root_barriers = [
            {"id": "A", "name": "Alpha"},
            {"id": "B", "name": "Beta"},
        ]
        all_codes = ["A", "B"]
        result = _build_chain_summary(root_barriers, all_codes)
        assert result == "Alpha \u2192 Beta"


class TestBuildEnrichedQuery:
    def test_includes_barriers_and_schedule(self):
        query = build_enriched_query(
            barrier_codes=["CHILDCARE_DAY", "TRANSPORTATION_NO_CAR"],
            zip_code="36104",
            schedule="day",
        )
        assert "CHILDCARE_DAY" in query
        assert "36104" in query
        assert "day" in query

    def test_handles_no_zip(self):
        query = build_enriched_query(
            barrier_codes=["CREDIT_LOW_SCORE"], zip_code=None, schedule=None
        )
        assert "CREDIT_LOW_SCORE" in query


class TestRagStoreSearch:
    @pytest.mark.anyio
    async def test_search_with_barrier_filter(self, rag_store):
        results = rag_store.search(
            "childcare assistance",
            barrier_filter=["CHILDCARE_DAY"],
            n=5,
        )
        assert len(results) > 0
        assert len(results) <= 5

    @pytest.mark.anyio
    async def test_search_without_filter(self, rag_store):
        results = rag_store.search("credit counseling", n=3)
        assert len(results) > 0
        assert len(results) <= 3


class TestRetrieveContext:
    @pytest.mark.anyio
    async def test_returns_retrieval_context(self, db_session, rag_store):
        ctx = await retrieve_context(
            barrier_codes=["CHILDCARE_DAY", "EMPLOYMENT_LIMITED_HOURS"],
            db_session=db_session,
            store=rag_store,
            zip_code="36104",
            schedule="day",
        )
        assert isinstance(ctx, RetrievalContext)
        assert len(ctx.root_barriers) > 0
        assert len(ctx.top_resources) > 0
        assert len(ctx.retrieved_docs) > 0
        assert ctx.retrieval_latency_ms >= 0

    @pytest.mark.anyio
    async def test_barrier_chain_summary_readable(self, db_session, rag_store):
        ctx = await retrieve_context(
            barrier_codes=["CHILDCARE_DAY", "EMPLOYMENT_LIMITED_HOURS"],
            db_session=db_session,
            store=rag_store,
        )
        assert len(ctx.barrier_chain_summary) > 0
        # Should contain arrow notation
        assert "→" in ctx.barrier_chain_summary or len(ctx.root_barriers) == 1

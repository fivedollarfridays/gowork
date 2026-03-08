"""Tests for T24.4 hybrid retrieval layer."""

import pytest

from app.rag.document_schema import RetrievalContext


# ---------------------------------------------------------------------------
# Cycle 1: RetrievalContext model
# ---------------------------------------------------------------------------

def test_retrieval_context_required_fields():
    from app.rag.document_schema import RagDocument

    doc = RagDocument(
        id="playbook_X", doc_type="playbook", title="T", text="text",
        barrier_tags=["X"],
    )
    ctx = RetrievalContext(
        root_barriers=["CHILDCARE_EVENING"],
        barrier_chain_summary="Childcare → Income Gap",
        top_resources=[{"id": 1, "name": "Resource A"}],
        retrieved_docs=[doc],
        user_zip="36104",
        user_schedule="day",
        retrieval_latency_ms=42.0,
    )
    assert ctx.root_barriers == ["CHILDCARE_EVENING"]
    assert ctx.retrieval_latency_ms == pytest.approx(42.0)


def test_retrieval_context_optional_fields():
    ctx = RetrievalContext(
        root_barriers=[],
        barrier_chain_summary="",
        top_resources=[],
        retrieved_docs=[],
        user_zip="36104",
        user_schedule=None,
        retrieval_latency_ms=0.0,
    )
    assert ctx.user_schedule is None


# ---------------------------------------------------------------------------
# Cycle 2: find_root_barriers BFS
# ---------------------------------------------------------------------------

pytestmark = pytest.mark.anyio


@pytest.mark.anyio
async def test_find_root_barriers_returns_roots_only(test_engine):
    """CHILDCARE_EVENING and TRANSPORTATION_NO_CAR have no incoming CAUSES edges."""
    from app.barrier_graph.traversal import find_root_barriers
    from app.core.database import get_async_session_factory

    factory = get_async_session_factory()
    async with factory() as db:
        roots = await find_root_barriers(
            ["CHILDCARE_EVENING", "TRANSPORTATION_NO_CAR"], db
        )
    root_ids = [r["id"] for r in roots]
    assert "CHILDCARE_EVENING" in root_ids
    assert "TRANSPORTATION_NO_CAR" in root_ids


@pytest.mark.anyio
async def test_find_root_barriers_excludes_downstream(test_engine):
    """EMPLOYMENT_LIMITED_HOURS is caused by CHILDCARE_EVENING — not a root."""
    from app.barrier_graph.traversal import find_root_barriers
    from app.core.database import get_async_session_factory

    factory = get_async_session_factory()
    async with factory() as db:
        roots = await find_root_barriers(
            ["CHILDCARE_EVENING", "EMPLOYMENT_LIMITED_HOURS"], db
        )
    root_ids = [r["id"] for r in roots]
    assert "CHILDCARE_EVENING" in root_ids
    assert "EMPLOYMENT_LIMITED_HOURS" not in root_ids


@pytest.mark.anyio
async def test_find_root_barriers_empty_input(test_engine):
    from app.barrier_graph.traversal import find_root_barriers
    from app.core.database import get_async_session_factory

    factory = get_async_session_factory()
    async with factory() as db:
        roots = await find_root_barriers([], db)
    assert roots == []


# ---------------------------------------------------------------------------
# Cycle 3: RagStore.search() — k limit + barrier_filter
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_rag_store_search_respects_k_limit(test_engine, tmp_path):
    from app.core.database import get_async_session_factory
    from app.rag.store import RagStore

    store = RagStore(index_dir=tmp_path)
    factory = get_async_session_factory()
    async with factory() as db:
        await store.build_or_load(db)

    results = store.search("childcare evening job help", k=3)
    assert len(results) <= 3


@pytest.mark.anyio
async def test_rag_store_search_with_barrier_filter_returns_relevant_docs(
    test_engine, tmp_path
):
    from app.core.database import get_async_session_factory
    from app.rag.store import RagStore

    store = RagStore(index_dir=tmp_path)
    factory = get_async_session_factory()
    async with factory() as db:
        await store.build_or_load(db)

    results = store.search(
        "childcare help", barrier_filter=["CHILDCARE_EVENING"], k=5
    )
    # All results must overlap with the filter
    for doc in results:
        assert any(tag in ["CHILDCARE_EVENING"] for tag in doc.barrier_tags)


# ---------------------------------------------------------------------------
# Cycle 4: retrieve_context — full assembly + latency
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_retrieve_context_returns_retrieval_context(test_engine, tmp_path):
    from app.core.database import get_async_session_factory
    from app.rag.document_schema import RetrievalContext
    from app.rag.retrieval import retrieve_context
    from app.rag.store import RagStore

    store = RagStore(index_dir=tmp_path)
    factory = get_async_session_factory()
    async with factory() as db:
        await store.build_or_load(db)
        ctx = await retrieve_context(
            barrier_ids=["CHILDCARE_EVENING", "TRANSPORTATION_NO_CAR"],
            user_zip="36104",
            user_schedule="day",
            db=db,
            store=store,
        )
    assert isinstance(ctx, RetrievalContext)
    assert ctx.retrieval_latency_ms >= 0
    assert ctx.user_zip == "36104"
    assert ctx.user_schedule == "day"


@pytest.mark.anyio
async def test_retrieve_context_latency_under_500ms(test_engine, tmp_path):
    from app.core.database import get_async_session_factory
    from app.rag.retrieval import retrieve_context
    from app.rag.store import RagStore

    store = RagStore(index_dir=tmp_path)
    factory = get_async_session_factory()
    async with factory() as db:
        await store.build_or_load(db)
        ctx = await retrieve_context(
            barrier_ids=["CHILDCARE_EVENING"],
            user_zip="36104",
            user_schedule=None,
            db=db,
            store=store,
        )
    assert ctx.retrieval_latency_ms < 500


@pytest.mark.anyio
async def test_retrieve_context_chain_summary_is_readable(test_engine, tmp_path):
    from app.core.database import get_async_session_factory
    from app.rag.retrieval import retrieve_context
    from app.rag.store import RagStore

    store = RagStore(index_dir=tmp_path)
    factory = get_async_session_factory()
    async with factory() as db:
        await store.build_or_load(db)
        ctx = await retrieve_context(
            barrier_ids=["CHILDCARE_EVENING", "TRANSPORTATION_NO_CAR"],
            user_zip="36104",
            user_schedule=None,
            db=db,
            store=store,
        )
    # Summary must be non-empty and contain "→" separator or at least a word
    assert len(ctx.barrier_chain_summary) > 0

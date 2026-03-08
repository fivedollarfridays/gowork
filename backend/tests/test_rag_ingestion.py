"""Tests for RAG knowledge base: document schema and FAISS ingestion pipeline."""

import pytest

from app.rag.document_schema import RagDocument


# ---------------------------------------------------------------------------
# Cycle 1: RagDocument schema
# ---------------------------------------------------------------------------

def test_rag_document_valid_resource():
    doc = RagDocument(
        id="resource_1",
        doc_type="resource",
        title="Some Resource",
        text="Helps people find jobs in Montgomery.",
        barrier_tags=["CHILDCARE_EVENING"],
        geography="Montgomery",
        schedule_type="day",
        transit_accessible=True,
        impact_strength=0.8,
    )
    assert doc.id == "resource_1"
    assert doc.doc_type == "resource"
    assert doc.transit_accessible is True
    assert doc.impact_strength == 0.8


def test_rag_document_optional_fields_default():
    doc = RagDocument(
        id="playbook_CHILDCARE",
        doc_type="playbook",
        title="Childcare Playbook",
        text="Connect client with DHR childcare voucher.",
        barrier_tags=["CHILDCARE_EVENING", "CHILDCARE_DAY"],
    )
    assert doc.geography is None
    assert doc.schedule_type is None
    assert doc.transit_accessible is False
    assert doc.impact_strength == 0.0


def test_rag_document_barrier_tags_required_non_empty():
    with pytest.raises(Exception):
        RagDocument(
            id="bad",
            doc_type="resource",
            title="Bad",
            text="text",
            barrier_tags=[],
        )


# ---------------------------------------------------------------------------
# Cycle 2: build_corpus() returns ≥30 docs with barrier_tags
# ---------------------------------------------------------------------------

pytestmark = pytest.mark.anyio


@pytest.mark.anyio
async def test_build_corpus_returns_minimum_docs(test_engine):
    from app.core.database import get_async_session_factory
    from app.rag.corpus_builder import build_corpus

    factory = get_async_session_factory()
    async with factory() as db:
        docs = await build_corpus(db)
    assert len(docs) >= 30


@pytest.mark.anyio
async def test_build_corpus_all_docs_have_barrier_tags(test_engine):
    from app.core.database import get_async_session_factory
    from app.rag.corpus_builder import build_corpus

    factory = get_async_session_factory()
    async with factory() as db:
        docs = await build_corpus(db)
    for doc in docs:
        assert len(doc.barrier_tags) > 0, f"Doc {doc.id} has empty barrier_tags"


@pytest.mark.anyio
async def test_build_corpus_includes_resource_and_playbook_docs(test_engine):
    from app.core.database import get_async_session_factory
    from app.rag.corpus_builder import build_corpus

    factory = get_async_session_factory()
    async with factory() as db:
        docs = await build_corpus(db)
    types = {d.doc_type for d in docs}
    assert "resource" in types
    assert "playbook" in types


# ---------------------------------------------------------------------------
# Cycle 3: FAISS index build — dimension 384
# ---------------------------------------------------------------------------

def test_build_index_returns_384_dim():
    from app.rag.ingestion import build_index

    docs = [
        RagDocument(
            id="playbook_X",
            doc_type="playbook",
            title="Test",
            text="Test document for embedding.",
            barrier_tags=["TEST"],
        )
    ]
    index, metadata = build_index(docs)
    assert index.d == 384


def test_build_index_metadata_matches_docs():
    from app.rag.ingestion import build_index

    docs = [
        RagDocument(
            id=f"playbook_{i}",
            doc_type="playbook",
            title=f"Doc {i}",
            text=f"Document number {i} for testing FAISS ingestion.",
            barrier_tags=["TAG"],
        )
        for i in range(3)
    ]
    index, metadata = build_index(docs)
    assert index.ntotal == 3
    assert len(metadata) == 3
    assert metadata[0]["id"] == "playbook_0"


# ---------------------------------------------------------------------------
# Cycle 4: save/load roundtrip preserves documents
# ---------------------------------------------------------------------------

def test_save_load_roundtrip_preserves_vector_count(tmp_path):
    from app.rag.ingestion import build_index, load_index, save_index

    docs = [
        RagDocument(
            id=f"playbook_{i}",
            doc_type="playbook",
            title=f"Doc {i}",
            text=f"Roundtrip test document {i}.",
            barrier_tags=["TAG"],
        )
        for i in range(5)
    ]
    index, metadata = build_index(docs)
    save_index(index, metadata, tmp_path)
    loaded_index, loaded_metadata = load_index(tmp_path)

    assert loaded_index.ntotal == 5
    assert len(loaded_metadata) == 5


def test_save_load_roundtrip_preserves_metadata_fields(tmp_path):
    from app.rag.ingestion import build_index, load_index, save_index

    docs = [
        RagDocument(
            id="resource_99",
            doc_type="resource",
            title="Test Resource",
            text="Helps with childcare.",
            barrier_tags=["CHILDCARE_EVENING"],
            geography="Montgomery",
            schedule_type="evening",
            transit_accessible=True,
            impact_strength=0.9,
        )
    ]
    index, metadata = build_index(docs)
    save_index(index, metadata, tmp_path)
    _, loaded_metadata = load_index(tmp_path)

    m = loaded_metadata[0]
    assert m["id"] == "resource_99"
    assert m["barrier_tags"] == ["CHILDCARE_EVENING"]
    assert m["geography"] == "Montgomery"
    assert m["transit_accessible"] is True
    assert m["impact_strength"] == pytest.approx(0.9)


# ---------------------------------------------------------------------------
# Cycle 5: RagStore singleton
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_rag_store_build_or_load_populates_store(test_engine, tmp_path):
    from app.core.database import get_async_session_factory
    from app.rag.store import RagStore

    store = RagStore(index_dir=tmp_path)
    factory = get_async_session_factory()
    async with factory() as db:
        await store.build_or_load(db)
    assert store.index is not None
    assert store.index.ntotal >= 30
    assert len(store.metadata) >= 30


@pytest.mark.anyio
async def test_rag_store_second_call_loads_from_disk(test_engine, tmp_path):
    from app.core.database import get_async_session_factory
    from app.rag.store import RagStore

    factory = get_async_session_factory()
    store1 = RagStore(index_dir=tmp_path)
    async with factory() as db:
        await store1.build_or_load(db)
    count1 = store1.index.ntotal

    store2 = RagStore(index_dir=tmp_path)
    async with factory() as db:
        await store2.build_or_load(db)
    assert store2.index.ntotal == count1


# ---------------------------------------------------------------------------
# Cycle 6: reindex endpoint requires X-Admin-Key
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_reindex_without_admin_key_returns_401_or_403(client):
    response = await client.post("/api/barrier-intel/reindex")
    assert response.status_code in (401, 403, 422)


@pytest.mark.anyio
async def test_reindex_with_wrong_admin_key_returns_403(client, monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setenv("ADMIN_API_KEY", "correct-key")
    get_settings.cache_clear()
    try:
        response = await client.post(
            "/api/barrier-intel/reindex",
            headers={"X-Admin-Key": "wrong-key"},
        )
        assert response.status_code == 403
    finally:
        get_settings.cache_clear()

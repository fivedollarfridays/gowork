"""Tests for RAG knowledge base: corpus builder, FAISS ingestion, and store."""

import pytest

from app.core.database import get_async_session_factory
from app.rag.corpus_builder import build_corpus
from app.rag.document_schema import RagDocument
from app.rag.ingestion import build_index, load_index, save_index
from app.rag.store import RagStore


@pytest.fixture
async def db_session(test_engine):
    factory = get_async_session_factory()
    async with factory() as session:
        yield session


class TestRagDocument:
    def test_create_document(self):
        doc = RagDocument(
            id="resource_1",
            doc_type="resource",
            title="Test Resource",
            text="Some text about this resource.",
            barrier_tags=["CHILDCARE_DAY"],
        )
        assert doc.id == "resource_1"
        assert doc.impact_strength == 0.0


class TestCorpusBuilder:
    @pytest.mark.anyio
    async def test_build_corpus_returns_documents(self, db_session):
        docs = await build_corpus(db_session)
        assert len(docs) >= 30

    @pytest.mark.anyio
    async def test_all_documents_have_barrier_tags(self, db_session):
        docs = await build_corpus(db_session)
        for doc in docs:
            assert len(doc.barrier_tags) > 0, f"{doc.id} has no barrier_tags"

    @pytest.mark.anyio
    async def test_corpus_includes_resources_and_playbooks(self, db_session):
        docs = await build_corpus(db_session)
        types = {d.doc_type for d in docs}
        assert "resource" in types
        assert "playbook" in types

    @pytest.mark.anyio
    async def test_resource_documents_have_text(self, db_session):
        docs = await build_corpus(db_session)
        resources = [d for d in docs if d.doc_type == "resource"]
        for r in resources:
            assert len(r.text) > 0


class TestFaissIngestion:
    @pytest.mark.anyio
    async def test_build_index_dimension_384(self, db_session):
        docs = await build_corpus(db_session)
        index, metadata = build_index(docs)
        assert index.d == 384

    @pytest.mark.anyio
    async def test_build_index_has_correct_count(self, db_session):
        docs = await build_corpus(db_session)
        index, metadata = build_index(docs)
        assert index.ntotal == len(docs)
        assert len(metadata) == len(docs)

    def test_save_and_load_roundtrip(self, tmp_path):
        docs = [
            RagDocument(
                id="test_1",
                doc_type="resource",
                title="Test",
                text="Test resource text for embedding.",
                barrier_tags=["CREDIT_LOW_SCORE"],
                impact_strength=0.8,
            ),
            RagDocument(
                id="test_2",
                doc_type="playbook",
                title="Test Playbook",
                text="Connect client with credit counseling service.",
                barrier_tags=["CREDIT_DEBT_HIGH"],
                impact_strength=0.9,
            ),
        ]
        index, metadata = build_index(docs)
        save_index(index, metadata, tmp_path)
        loaded_index, loaded_meta = load_index(tmp_path)
        assert loaded_index.d == 384
        assert loaded_index.ntotal == 2
        assert len(loaded_meta) == 2
        assert loaded_meta[0]["id"] == "test_1"
        assert loaded_meta[1]["id"] == "test_2"


class TestRagStore:
    @pytest.mark.anyio
    async def test_build_or_load_creates_store(self, db_session, tmp_path):
        store = RagStore()
        await store.build_or_load(db_session, index_dir=tmp_path)
        assert store.is_ready()

    @pytest.mark.anyio
    async def test_search_returns_results(self, db_session, tmp_path):
        store = RagStore()
        await store.build_or_load(db_session, index_dir=tmp_path)
        results = store.search("childcare assistance", n=3)
        assert len(results) <= 3
        assert len(results) > 0

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


class TestExtractCity:
    """Cover _extract_city edge cases in corpus_builder.py."""

    def test_extract_city_returns_none_for_none(self):
        from app.rag.corpus_builder import _extract_city

        assert _extract_city(None) is None

    def test_extract_city_returns_none_for_empty_string(self):
        from app.rag.corpus_builder import _extract_city

        assert _extract_city("") is None

    def test_extract_city_no_comma_returns_none(self):
        from app.rag.corpus_builder import _extract_city

        assert _extract_city("Montgomery") is None

    def test_extract_city_with_full_address(self):
        from app.rag.corpus_builder import _extract_city

        assert _extract_city("100 Main St, Montgomery, AL") == "Montgomery"

    def test_extract_city_two_part_address(self):
        from app.rag.corpus_builder import _extract_city

        assert _extract_city("100 Main St, Montgomery") == "100 Main St"


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

    def test_search_not_ready_returns_empty(self):
        """Search on a store that has not been built returns empty list."""
        store = RagStore()
        results = store.search("anything")
        assert results == []

    @pytest.mark.anyio
    async def test_rebuild_no_docs_returns_zero(self, db_session, tmp_path):
        """When build_corpus returns no docs, rebuild returns 0."""
        from unittest.mock import AsyncMock, patch

        store = RagStore()
        with patch("app.rag.store.build_corpus", new_callable=AsyncMock, return_value=[]):
            count = await store.rebuild(db_session, index_dir=tmp_path)
        assert count == 0
        assert not store.is_ready()

    @pytest.mark.anyio
    async def test_build_or_load_from_disk(self, db_session, tmp_path):
        """When index.faiss exists on disk, build_or_load loads from disk."""
        # First, build and save to disk
        store1 = RagStore()
        await store1.build_or_load(db_session, index_dir=tmp_path)
        assert store1.is_ready()

        # Now create a second store and load from disk
        store2 = RagStore()
        await store2.build_or_load(db_session, index_dir=tmp_path)
        assert store2.is_ready()

    @pytest.mark.anyio
    async def test_search_with_barrier_filter_excludes_non_matching(self, db_session, tmp_path):
        """Search with barrier_filter skips docs whose tags do not overlap."""
        store = RagStore()
        await store.build_or_load(db_session, index_dir=tmp_path)

        # Search with a filter that is very specific
        results = store.search(
            "credit counseling help", n=5,
            barrier_filter=["CREDIT_LOW_SCORE"],
        )
        for r in results:
            # Every returned doc must have at least one tag in the filter set
            assert "CREDIT_LOW_SCORE" in r.get("barrier_tags", [])

    def test_search_skips_negative_faiss_indices(self):
        """FAISS returning -1 indices (padding) should be skipped."""
        from unittest.mock import MagicMock, patch

        import numpy as np

        store = RagStore()
        store._index = MagicMock()
        store._index.ntotal = 2
        store._index.search.return_value = (
            np.array([[0.9, 0.8, -1.0]], dtype=np.float32),
            np.array([[0, 1, -1]], dtype=np.int64),
        )
        store._metadata = [
            {"id": "doc_0", "barrier_tags": []},
            {"id": "doc_1", "barrier_tags": []},
        ]

        with patch("app.rag.store._get_model") as mock_model:
            mock_model.return_value.encode.return_value = (
                np.array([[0.1] * 384], dtype=np.float32)
            )
            results = store.search("test query", n=5)

        assert len(results) == 2
        assert {r["id"] for r in results} == {"doc_0", "doc_1"}

"""RagStore — singleton holding the in-memory FAISS index + metadata."""

import logging
from pathlib import Path

import faiss
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession

from app.rag.corpus_builder import build_corpus
from app.rag.document_schema import RagDocument
from app.rag.ingestion import _get_model, build_index, load_index, save_index

logger = logging.getLogger(__name__)

_DEFAULT_INDEX_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "rag_index"

# Module-level singleton used by the app
_store: "RagStore | None" = None


def get_rag_store() -> "RagStore":
    """Return the global RagStore instance (must call build_or_load first)."""
    if _store is None:
        raise RuntimeError("RagStore not initialized — call build_or_load on startup")
    return _store


class RagStore:
    """Holds the FAISS index and document metadata for barrier-intel retrieval."""

    def __init__(self, index_dir: Path | None = None) -> None:
        self.index_dir = index_dir or _DEFAULT_INDEX_DIR
        self.index: faiss.IndexFlatIP | None = None
        self.metadata: list[dict] = []

    async def build_or_load(self, db: AsyncSession) -> None:
        """Load existing index from disk or rebuild from DB and save."""
        index_file = self.index_dir / "index.faiss"
        metadata_file = self.index_dir / "metadata.json"

        if index_file.exists() and metadata_file.exists():
            self.index, self.metadata = load_index(self.index_dir)
            return

        docs = await build_corpus(db)
        self.index, self.metadata = build_index(docs)
        save_index(self.index, self.metadata, self.index_dir)

    def search(
        self,
        query: str,
        barrier_filter: list[str] | None = None,
        k: int = 8,
    ) -> list[RagDocument]:
        """Embed query, search FAISS, post-filter by barrier_tags overlap."""
        if self.index is None or self.index.ntotal == 0:
            return []
        model = _get_model()
        vec = model.encode([query], convert_to_numpy=True, normalize_embeddings=True)
        vec = vec.astype(np.float32)
        fetch_k = k * 2 if barrier_filter else k
        fetch_k = min(fetch_k, self.index.ntotal)
        _, indices = self.index.search(vec, fetch_k)
        results: list[RagDocument] = []
        for idx in indices[0]:
            if idx < 0 or idx >= len(self.metadata):
                continue
            m = self.metadata[idx]
            if barrier_filter and not set(m["barrier_tags"]) & set(barrier_filter):
                continue
            results.append(RagDocument(**m, text=""))
            if len(results) >= k:
                break
        return results

    async def rebuild(self, db: AsyncSession) -> None:
        """Force rebuild of the index from DB, overwriting any cached files."""
        docs = await build_corpus(db)
        self.index, self.metadata = build_index(docs)
        save_index(self.index, self.metadata, self.index_dir)
        logger.info("RagStore rebuilt: %d documents", len(self.metadata))


async def init_rag_store(db: AsyncSession, index_dir: Path | None = None) -> RagStore:
    """Initialize and populate the global RagStore singleton."""
    global _store
    _store = RagStore(index_dir=index_dir)
    await _store.build_or_load(db)
    return _store

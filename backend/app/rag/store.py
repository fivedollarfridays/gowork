"""RAG store singleton — holds FAISS index and metadata in memory."""

import logging
from pathlib import Path

import faiss
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession

from app.rag.corpus_builder import build_corpus
from app.rag.ingestion import _get_model, build_index, load_index, save_index

logger = logging.getLogger(__name__)

_DEFAULT_INDEX_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "rag_index"


class RagStore:
    """In-memory FAISS index + metadata for barrier intelligence queries."""

    def __init__(self) -> None:
        self._index: faiss.Index | None = None
        self._metadata: list[dict] = []

    def is_ready(self) -> bool:
        """Return True if index is loaded and ready for queries."""
        return self._index is not None and self._index.ntotal > 0

    async def build_or_load(
        self, session: AsyncSession, index_dir: Path | None = None
    ) -> None:
        """Build index from DB or load from disk if fresh."""
        index_dir = Path(index_dir) if index_dir else _DEFAULT_INDEX_DIR
        index_file = index_dir / "index.faiss"

        if index_file.exists():
            self._index, self._metadata = load_index(index_dir)
            return

        await self.rebuild(session, index_dir)

    async def rebuild(
        self, session: AsyncSession, index_dir: Path | None = None
    ) -> int:
        """Force rebuild from database. Returns document count."""
        index_dir = Path(index_dir) if index_dir else _DEFAULT_INDEX_DIR
        docs = await build_corpus(session)
        if not docs:
            logger.warning("No documents found for RAG index")
            return 0
        self._index, self._metadata = build_index(docs)
        save_index(self._index, self._metadata, index_dir)
        return len(docs)

    def search(
        self, query: str, n: int = 5, barrier_filter: list[str] | None = None
    ) -> list[dict]:
        """Search the index for documents matching the query.

        When barrier_filter is provided, fetches extra candidates then post-filters
        to docs whose barrier_tags overlap the filter set.
        """
        if not self.is_ready():
            return []

        model = _get_model()
        query_vec = model.encode([query], normalize_embeddings=True)
        query_vec = np.array(query_vec, dtype=np.float32)

        fetch_k = min(n * 3, self._index.ntotal) if barrier_filter else n
        fetch_k = min(fetch_k, self._index.ntotal)
        distances, indices = self._index.search(query_vec, fetch_k)

        filter_set = set(barrier_filter) if barrier_filter else None
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0:
                continue
            meta = self._metadata[idx].copy()
            meta["score"] = float(dist)
            if filter_set:
                doc_tags = set(meta.get("barrier_tags", []))
                if not doc_tags & filter_set:
                    continue
            results.append(meta)
            if len(results) >= n:
                break
        return results

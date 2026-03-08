"""FAISS index build, save, and load for the RAG knowledge base."""

import json
import logging
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from app.rag.document_schema import RagDocument

logger = logging.getLogger(__name__)

_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
_DIM = 384

_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(_MODEL_NAME)
    return _model


def build_index(docs: list[RagDocument]) -> tuple[faiss.IndexFlatIP, list[dict]]:
    """Embed documents and build a FAISS IndexFlatIP (cosine via L2-norm)."""
    model = _get_model()
    texts = [doc.text for doc in docs]
    embeddings = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
    embeddings = embeddings.astype(np.float32)

    index = faiss.IndexFlatIP(_DIM)
    index.add(embeddings)

    metadata = [
        {
            "id": doc.id,
            "doc_type": doc.doc_type,
            "title": doc.title,
            "barrier_tags": doc.barrier_tags,
            "geography": doc.geography,
            "schedule_type": doc.schedule_type,
            "transit_accessible": doc.transit_accessible,
            "impact_strength": doc.impact_strength,
        }
        for doc in docs
    ]
    return index, metadata


def save_index(
    index: faiss.IndexFlatIP,
    metadata: list[dict],
    index_dir: Path,
) -> None:
    """Persist FAISS index and metadata to disk."""
    index_dir.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(index_dir / "index.faiss"))
    (index_dir / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False), encoding="utf-8"
    )
    logger.info("Saved FAISS index (%d vectors) to %s", index.ntotal, index_dir)


def load_index(index_dir: Path) -> tuple[faiss.IndexFlatIP, list[dict]]:
    """Load FAISS index and metadata from disk."""
    index = faiss.read_index(str(index_dir / "index.faiss"))
    metadata = json.loads((index_dir / "metadata.json").read_text(encoding="utf-8"))
    logger.info("Loaded FAISS index (%d vectors) from %s", index.ntotal, index_dir)
    return index, metadata

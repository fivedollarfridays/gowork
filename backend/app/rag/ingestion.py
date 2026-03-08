"""FAISS index build, save, and load for RAG knowledge base."""

import json
import logging
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from app.rag.document_schema import RagDocument

logger = logging.getLogger(__name__)

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
DIMENSION = 384

_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    """Lazy-load the sentence transformer model."""
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def build_index(
    documents: list[RagDocument],
) -> tuple[faiss.Index, list[dict]]:
    """Embed documents and build a FAISS IndexFlatIP (cosine similarity)."""
    model = _get_model()
    texts = [doc.text for doc in documents]
    embeddings = model.encode(texts, normalize_embeddings=True)
    embeddings = np.array(embeddings, dtype=np.float32)

    index = faiss.IndexFlatIP(DIMENSION)
    index.add(embeddings)

    metadata = [doc.model_dump() for doc in documents]
    logger.info("Built FAISS index: %d documents, dim=%d", index.ntotal, DIMENSION)
    return index, metadata


def save_index(index: faiss.Index, metadata: list[dict], path: Path) -> None:
    """Persist FAISS index and metadata to disk."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(path / "index.faiss"))
    (path / "metadata.json").write_text(json.dumps(metadata))
    logger.info("Saved FAISS index to %s", path)


def load_index(path: Path) -> tuple[faiss.Index, list[dict]]:
    """Load FAISS index and metadata from disk."""
    path = Path(path)
    index = faiss.read_index(str(path / "index.faiss"))
    metadata = json.loads((path / "metadata.json").read_text())
    logger.info("Loaded FAISS index from %s: %d docs", path, index.ntotal)
    return index, metadata

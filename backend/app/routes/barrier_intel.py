"""Barrier Intelligence API — RAG-powered barrier assistant endpoints."""

import logging

from fastapi import APIRouter, Depends

from app.core.auth import require_admin_key
from app.core.database import get_async_session_factory
from app.rag.store import get_rag_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/barrier-intel", tags=["barrier-intel"])


@router.post("/reindex", dependencies=[Depends(require_admin_key)])
async def reindex():
    """Force-rebuild the RAG FAISS index from the current DB state."""
    store = get_rag_store()
    factory = get_async_session_factory()
    async with factory() as db:
        await store.rebuild(db)
    return {"status": "ok", "documents": len(store.metadata)}

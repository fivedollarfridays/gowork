"""Barrier Intelligence chat endpoint with SSE streaming."""

import json

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.barrier_intel.cache import get_cache_key, get_cached_retrieval, set_cached_retrieval
from app.barrier_intel.guardrails import SAFE_FALLBACK, is_disallowed_topic
from app.barrier_intel.schemas import ChatRequest
from app.barrier_intel.streaming import stream_chat_response
from app.core.auth import require_admin_key
from app.core.database import get_db
from app.core.queries import get_session_by_id
from app.core.rate_limit import RateLimiter, require_rate_limit
from app.rag.document_schema import RetrievalContext
from app.rag.retrieval import retrieve_context

router = APIRouter(prefix="/api/barrier-intel", tags=["barrier-intel"])
_rate_limiter = RateLimiter(max_requests=10, window_seconds=60)
_check_rate = require_rate_limit(_rate_limiter)


@router.post("/reindex", dependencies=[Depends(require_admin_key)])
async def reindex(request: Request, db=Depends(get_db)):
    """Force rebuild the RAG index from database."""
    store = request.app.state.rag_store
    count = await store.rebuild(db)
    return {"status": "ok", "documents_indexed": count}


async def _get_retrieval_ctx(cache_key, barriers, db, store, profile) -> RetrievalContext:
    """Fetch retrieval context, using cache when available."""
    cached = get_cached_retrieval(cache_key)
    if cached:
        return cached
    ctx = await retrieve_context(
        barrier_codes=barriers,
        db_session=db,
        store=store,
        zip_code=profile.get("zip_code"),
        schedule=profile.get("schedule"),
    )
    set_cached_retrieval(cache_key, ctx)
    return ctx


@router.post("/chat", dependencies=[Depends(_check_rate)])
async def chat(body: ChatRequest, request: Request, db=Depends(get_db)):
    """Barrier intelligence chat with SSE streaming."""
    session = await get_session_by_id(db, body.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    if is_disallowed_topic(body.user_question):
        return {"message": SAFE_FALLBACK, "guardrail_triggered": True}

    store = request.app.state.rag_store
    barriers = json.loads(session["barriers"])
    profile = json.loads(session.get("profile") or "{}")
    cache_key = get_cache_key(body.session_id, body.user_question, body.mode)
    ctx = await _get_retrieval_ctx(cache_key, barriers, db, store, profile)

    return StreamingResponse(
        stream_chat_response(
            question=body.user_question,
            mode=body.mode,
            ctx=ctx,
            session_hash=cache_key[:12],
        ),
        media_type="text/event-stream",
    )

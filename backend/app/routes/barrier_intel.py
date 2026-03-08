"""Barrier Intelligence API — RAG-powered barrier assistant endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.barrier_intel.audit_log import write_audit_entry
from app.barrier_intel.guardrails import SAFE_FALLBACK, is_disallowed_topic
from app.barrier_intel.schemas import ChatRequest
from app.barrier_intel.stream import format_sse, stream_chat
from app.core.auth import require_admin_key
from app.core.database import get_async_session_factory
from app.core.queries import get_session_by_id
from app.core.rate_limit import RateLimiter, require_rate_limit
from app.rag.store import get_rag_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/barrier-intel", tags=["barrier-intel"])

_chat_limiter = RateLimiter(max_requests=10, window_seconds=60)


async def _guardrail_response(body: ChatRequest) -> StreamingResponse:
    write_audit_entry(
        session_id=body.session_id, mode=body.mode, root_barriers=[],
        retrieval_doc_ids=[], input_tokens=0, output_tokens=0,
        latency_ms=0.0, guardrail_triggered=True,
    )

    async def _fallback():
        yield format_sse("token", {"text": SAFE_FALLBACK})
        yield format_sse("done", {"usage": {"input_tokens": 0, "output_tokens": 0}})

    return StreamingResponse(_fallback(), media_type="text/event-stream")


@router.post("/chat")
async def chat(
    body: ChatRequest,
    request: Request,
    _rate: None = Depends(require_rate_limit(_chat_limiter)),
):
    """Stream barrier intelligence response as SSE."""
    if is_disallowed_topic(body.user_question):
        return await _guardrail_response(body)

    factory = get_async_session_factory()
    async with factory() as db:
        session_row = await get_session_by_id(db, body.session_id)
    if not session_row:
        raise HTTPException(status_code=404, detail="Session not found")

    store = get_rag_store()
    return StreamingResponse(
        stream_chat(body, session_row, store),
        media_type="text/event-stream",
    )


@router.post("/reindex", dependencies=[Depends(require_admin_key)])
async def reindex():
    """Force-rebuild the RAG FAISS index from the current DB state."""
    store = get_rag_store()
    factory = get_async_session_factory()
    async with factory() as db:
        await store.rebuild(db)
    return {"status": "ok", "documents": len(store.metadata)}

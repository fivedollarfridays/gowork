"""SSE streaming handler for barrier intelligence chat."""

import json
import logging
import time

logger = logging.getLogger(__name__)

from app.barrier_intel.audit_log import write_audit_entry
from app.barrier_intel.llm_client import get_llm_stream
from app.barrier_intel.prompts import build_context_event, build_user_prompt
from app.barrier_intel.schemas import ChatRequest
from app.core.database import get_async_session_factory
from app.rag.retrieval import retrieve_context
from app.rag.store import RagStore


def format_sse(event_type: str, payload: dict) -> str:
    return f"data: {json.dumps({'type': event_type, **payload})}\n\n"


def _parse_session_profile(session_row: dict) -> tuple[list, str, str | None]:
    barriers = json.loads(session_row.get("barriers") or "[]")
    profile = json.loads(session_row.get("profile") or "{}")
    user_zip = profile.get("zip_code", "36104")
    user_schedule = profile.get("schedule_preference")
    return barriers, user_zip, user_schedule


async def stream_chat(
    body: ChatRequest,
    session_row: dict,
    store: RagStore,
):
    """Async generator: context event → token events → done event."""
    t0 = time.monotonic()
    barriers, user_zip, user_schedule = _parse_session_profile(session_row)
    factory = get_async_session_factory()
    async with factory() as db:
        ctx = await retrieve_context(
            barrier_ids=barriers, user_zip=user_zip,
            user_schedule=user_schedule, db=db, store=store,
        )
    yield format_sse("context", build_context_event(ctx))

    user_prompt = build_user_prompt(body.user_question, body.mode, ctx)
    input_tokens = output_tokens = 0
    try:
        async for text, in_tok, out_tok in get_llm_stream(user_prompt):
            if text:
                yield format_sse("token", {"text": text})
            if in_tok:
                input_tokens, output_tokens = in_tok, out_tok
    except Exception as exc:
        logger.error("LLM stream error: %s", exc)
        yield format_sse("error", {"message": _friendly_error(exc)})
        yield format_sse("done", {"usage": {"input_tokens": 0, "output_tokens": 0}})
        return

    yield format_sse("done", {"usage": {"input_tokens": input_tokens, "output_tokens": output_tokens}})
    latency_ms = (time.monotonic() - t0) * 1000
    write_audit_entry(
        session_id=body.session_id, mode=body.mode,
        root_barriers=ctx.root_barriers,
        retrieval_doc_ids=[d.id for d in ctx.retrieved_docs],
        input_tokens=input_tokens, output_tokens=output_tokens,
        latency_ms=latency_ms, guardrail_triggered=False,
    )


def _friendly_error(exc: Exception) -> str:
    msg = str(exc).lower()
    if "401" in msg or "authentication" in msg or "invalid" in msg and "key" in msg:
        return "Invalid API key. Check your LLM provider key in .env and restart the server."
    if "429" in msg or "rate" in msg:
        return "Rate limit reached. Please wait a moment and try again."
    if "quota" in msg or "billing" in msg:
        return "API quota exceeded. Check your provider billing settings."
    return "The AI service is temporarily unavailable. Please try again."

"""SSE streaming helpers for barrier intelligence chat."""

import json
import logging
import time

from app.ai.audit_log import log_llm_interaction
from app.ai.llm_client import get_llm_stream
from app.barrier_intel.guardrails import check_hallucinations
from app.barrier_intel.observability import build_request_log
from app.barrier_intel.prompts import SYSTEM_PROMPT, build_user_prompt
from app.core.config import get_settings
from app.rag.document_schema import RetrievalContext

logger = logging.getLogger(__name__)


def format_sse(event_type: str, data: dict | str) -> str:
    """Format a server-sent event."""
    payload = json.dumps({"type": event_type, **(data if isinstance(data, dict) else {"text": data})})
    return f"data: {payload}\n\n"


async def stream_chat_response(
    question: str,
    mode: str,
    ctx: RetrievalContext,
    session_hash: str,
):
    """Async generator yielding SSE events for the chat response."""
    start = time.monotonic()
    barrier_ids = [b["id"] for b in ctx.root_barriers]
    ctx_event = {
        "root_barriers": barrier_ids,
        "chain": ctx.barrier_chain_summary,
    }
    yield format_sse("context", ctx_event)

    user_prompt = build_user_prompt(question, mode, ctx)
    chunk_count = 0
    collected_text = []
    async for text in get_llm_stream(SYSTEM_PROMPT, user_prompt):
        yield format_sse("token", {"text": text})
        collected_text.append(text)
        chunk_count += 1

    guardrail_triggered = False
    full_response = "".join(collected_text)
    known_names = [r["name"] for r in ctx.top_resources]
    disclaimer = check_hallucinations(full_response, known_names)
    if disclaimer:
        guardrail_triggered = True
        yield format_sse("disclaimer", {"text": disclaimer})

    latency_ms = (time.monotonic() - start) * 1000
    yield format_sse("done", {"chunks": chunk_count, "latency_ms": round(latency_ms)})

    full_prompt_len = len(user_prompt)
    await _audit_log(
        session_hash, mode, barrier_ids, ctx, chunk_count, latency_ms,
        guardrail_triggered=guardrail_triggered,
        prompt_length=full_prompt_len,
        response_length=len(full_response),
    )


async def _audit_log(
    session_hash: str,
    mode: str,
    barrier_ids: list[str],
    ctx: RetrievalContext,
    chunk_count: int,
    latency_ms: float,
    *,
    guardrail_triggered: bool = False,
    prompt_length: int = 0,
    response_length: int = 0,
) -> None:
    """PII-safe structured audit log entry."""
    log_data = build_request_log(
        session_hash=session_hash,
        mode=mode,
        root_barriers=barrier_ids,
        retrieval_doc_count=len(ctx.retrieved_docs),
        retrieval_latency_ms=ctx.retrieval_latency_ms,
        llm_latency_ms=latency_ms,
        input_tokens=prompt_length,
        output_tokens=response_length,
        cache_hit=False,
        guardrail_triggered=guardrail_triggered,
    )
    logger.info("barrier_intel_chat", extra=log_data)

    settings = get_settings()
    await log_llm_interaction(
        log_path=settings.audit_log_path,
        session_id=session_hash,
        provider=settings.llm_provider,
        prompt_length=prompt_length,
        response_length=response_length,
        latency_ms=latency_ms,
    )

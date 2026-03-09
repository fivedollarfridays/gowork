"""SSE streaming helpers for barrier intelligence chat."""

import json
import logging
import time
from typing import Literal

from app.ai.audit_log import log_llm_interaction
from app.ai.llm_client import get_llm_stream, resolve_provider
from app.barrier_intel.guardrails import check_hallucinations
from app.barrier_intel.observability import build_request_log
from app.barrier_intel.prompts import SYSTEM_PROMPT, build_user_prompt
from app.core.config import get_settings
from app.rag.document_schema import RetrievalContext

ChatMode = Literal["next_steps", "explain_plan"]

logger = logging.getLogger(__name__)


def format_sse(event_type: str, data: dict | str) -> str:
    """Format a server-sent event."""
    payload = json.dumps({"type": event_type, **(data if isinstance(data, dict) else {"text": data})})
    return f"data: {payload}\n\n"


async def stream_chat_response(
    question: str,
    mode: ChatMode,
    ctx: RetrievalContext,
    session_hash: str,
):
    """Async generator yielding SSE events for the chat response."""
    start = time.monotonic()
    provider = resolve_provider()
    barrier_ids = [b["id"] for b in ctx.root_barriers]
    yield format_sse("context", {"root_barriers": barrier_ids, "chain": ctx.barrier_chain_summary})

    user_prompt = build_user_prompt(question, mode, ctx)
    chunk_count = 0
    collected_text: list[str] = []
    async for text in get_llm_stream(SYSTEM_PROMPT, user_prompt, provider=provider):
        yield format_sse("token", {"text": text})
        collected_text.append(text)
        chunk_count += 1

    full_response = "".join(collected_text)
    guardrail_triggered, disclaimer = _check_response(full_response, ctx)
    if disclaimer:
        yield format_sse("disclaimer", {"text": disclaimer})

    latency_ms = (time.monotonic() - start) * 1000
    yield format_sse("done", {"chunks": chunk_count, "latency_ms": round(latency_ms)})

    await _audit_log(
        session_hash, provider, mode, barrier_ids, ctx,
        chunk_count, latency_ms,
        guardrail_triggered=guardrail_triggered,
        prompt_length=len(user_prompt),
        response_length=len(full_response),
    )


def _check_response(response: str, ctx: RetrievalContext) -> tuple[bool, str | None]:
    """Check response for hallucinations. Returns (triggered, disclaimer)."""
    known_names = [r.get("name", r.get("title", "")) for r in ctx.top_resources]
    disclaimer = check_hallucinations(response, known_names)
    return (True, disclaimer) if disclaimer else (False, None)

async def _audit_log(
    session_hash: str,
    provider: str,
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
        prompt_chars=prompt_length,
        response_chars=response_length,
        cache_hit=False,
        guardrail_triggered=guardrail_triggered,
    )
    logger.info("barrier_intel_chat", extra=log_data)

    settings = get_settings()
    await log_llm_interaction(
        log_path=settings.audit_log_path,
        session_id=session_hash,
        provider=provider,
        prompt_length=prompt_length,
        response_length=response_length,
        latency_ms=latency_ms,
    )

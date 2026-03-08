"""SSE streaming helpers for barrier intelligence chat."""

import json
import logging
import time

import anthropic

from app.barrier_intel.observability import build_request_log
from app.barrier_intel.prompts import SYSTEM_PROMPT, build_user_prompt
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
    api_key: str,
    model: str,
    session_hash: str,
):
    """Async generator yielding SSE events for the chat response."""
    start = time.monotonic()
    ctx_event = {
        "root_barriers": [b["id"] for b in ctx.root_barriers],
        "chain": ctx.barrier_chain_summary,
    }
    yield format_sse("context", ctx_event)

    user_prompt = build_user_prompt(question, mode, ctx)
    client = anthropic.AsyncAnthropic(api_key=api_key)
    async with client.messages.stream(
        model=model,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    ) as stream:
        async for text in stream.text_stream:
            yield format_sse("token", {"text": text})
        response = await stream.get_final_message()

    usage = {
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
    }
    latency_ms = (time.monotonic() - start) * 1000
    yield format_sse("done", {"usage": usage, "latency_ms": round(latency_ms)})

    _audit_log(session_hash, mode, ctx, usage, latency_ms)


def _audit_log(
    session_hash: str,
    mode: str,
    ctx: RetrievalContext,
    usage: dict,
    latency_ms: float,
) -> None:
    """PII-safe structured audit log entry."""
    log_data = build_request_log(
        session_hash=session_hash,
        mode=mode,
        root_barriers=[b["id"] for b in ctx.root_barriers],
        retrieval_doc_count=len(ctx.retrieved_docs),
        retrieval_latency_ms=ctx.retrieval_latency_ms,
        llm_latency_ms=latency_ms,
        input_tokens=usage.get("input_tokens", 0),
        output_tokens=usage.get("output_tokens", 0),
        cache_hit=False,
        guardrail_triggered=False,
    )
    logger.info("barrier_intel_chat", extra=log_data)

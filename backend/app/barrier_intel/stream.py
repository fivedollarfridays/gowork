"""SSE streaming handler for barrier intelligence chat."""

import json
import time

from anthropic import AsyncAnthropic

from app.barrier_intel.audit_log import write_audit_entry
from app.barrier_intel.prompts import SYSTEM_PROMPT, build_context_event, build_user_prompt
from app.barrier_intel.schemas import ChatRequest
from app.core.config import get_settings
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


async def _call_claude_stream(user_prompt: str):
    """Yield (text_chunks, input_tokens, output_tokens) via async gen."""
    settings = get_settings()
    client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    async with client.messages.stream(
        model=settings.claude_model,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    ) as stream:
        async for text in stream.text_stream:
            yield text, 0, 0
        final = await stream.get_final_message()
        yield "", final.usage.input_tokens, final.usage.output_tokens


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
    async for text, in_tok, out_tok in _call_claude_stream(user_prompt):
        if text:
            yield format_sse("token", {"text": text})
        if in_tok:
            input_tokens, output_tokens = in_tok, out_tok

    yield format_sse("done", {"usage": {"input_tokens": input_tokens, "output_tokens": output_tokens}})
    latency_ms = (time.monotonic() - t0) * 1000
    write_audit_entry(
        session_id=body.session_id, mode=body.mode,
        root_barriers=ctx.root_barriers,
        retrieval_doc_ids=[d.id for d in ctx.retrieved_docs],
        input_tokens=input_tokens, output_tokens=output_tokens,
        latency_ms=latency_ms, guardrail_triggered=False,
    )

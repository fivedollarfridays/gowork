"""Haiku-augmented "Explain My Match" composer.

Pipeline:
1. Caller passes a job dict + score_breakdown + retrieved RAG docs.
2. We prompt Haiku to write a 2-paragraph natural-language explanation
   that grounds the score in the user's barriers + cites real resources.
3. On any failure the deterministic fallback composes a one-paragraph
   summary from the same inputs so the UI always has something to show.

Cache: keyed by (session_id, job_signature).  Same explanation served
instantly on subsequent clicks within 24h.
"""

from __future__ import annotations

import logging
from typing import Any

from app.integrations.llm._cache import match_explanation_cache
from app.integrations.llm._haiku_client import HaikuError, call_haiku
from app.integrations.llm._match_explainer_prompts import (
    SYSTEM_PROMPT,
    build_fallback,
    build_user_prompt,
    job_signature,
)

logger = logging.getLogger(__name__)

_MAX_TOKENS = 500


async def explain_match(
    *,
    session_id: str,
    job: dict[str, Any],
    score_breakdown: dict | None,
    barriers: list[str],
    retrieved_docs: list[dict],
) -> dict:
    """Return ``{"text": str, "source": "haiku"|"fallback", "cached": bool}``.

    Always returns a dict — never raises.  ``source`` is "haiku" only when
    the LLM produced the text; "fallback" indicates deterministic output.
    """
    cache_key = f"{session_id}|{job_signature(job)}"
    cached = match_explanation_cache.get(cache_key)
    if cached:
        return {"text": cached, "source": "haiku", "cached": True}

    user_prompt = build_user_prompt(job, score_breakdown, barriers, retrieved_docs)
    try:
        result = await call_haiku(SYSTEM_PROMPT, user_prompt, max_tokens=_MAX_TOKENS)
    except HaikuError as exc:
        logger.warning("match_explainer falling back: %s", exc)
        text = build_fallback(job, score_breakdown, barriers, retrieved_docs)
        return {"text": text, "source": "fallback", "cached": False}

    match_explanation_cache.set(cache_key, result.text)
    logger.info(
        "match_explainer haiku ok session=%s tokens_in=%d tokens_out=%d cost~$%.4f",
        session_id, result.input_tokens, result.output_tokens,
        result.estimated_cost_usd,
    )
    return {"text": result.text, "source": "haiku", "cached": False}

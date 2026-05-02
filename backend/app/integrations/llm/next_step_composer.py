"""Haiku-augmented Monday-morning next-step composer.

The deterministic ``_build_next_steps`` produces solid but template-y steps:
"Contact Trinity Metro for transportation support."  This composer enriches
that with a specific action sequence Haiku grounds in:
1. The user's barriers
2. The retrieved RAG docs (Trinity Metro routes, TWC addresses, hours)
3. The deterministic baseline (so we never lose the canonical contacts)

Output is a list[str] — same shape as the deterministic output — so the
caller can drop it into ``ReEntryPlan.immediate_next_steps`` unchanged.

Cache: keyed by session_id (24h TTL).  Replays return the same ordered list.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from app.integrations.llm._cache import next_step_cache
from app.integrations.llm._haiku_client import HaikuError, call_haiku

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are a workforce navigator for Fort Worth, TX. Your job is to write "
    "a Monday-morning action sequence for ONE resident with specific "
    "barriers. Each step is ONE sentence, starts with a verb, and names a "
    "real Fort Worth resource (Trinity Metro, Workforce Solutions for "
    "Tarrant County, Tarrant Area Food Bank, etc.) — NEVER invent an "
    "address, phone, or program that wasn't in the retrieved context. "
    "Output exactly 4 steps, one per line, no numbering, no bullets, no "
    "preamble. Address the resident as 'you'."
)
_MAX_TOKENS = 350
_MAX_STEPS = 4


def _format_docs(docs: list[dict]) -> str:
    if not docs:
        return "(no resources retrieved — refer the user to Workforce Solutions for Tarrant County, 1200 Circle Dr.)"
    lines: list[str] = []
    for i, doc in enumerate(docs[:5], start=1):
        title = doc.get("title") or doc.get("name") or "Resource"
        text = (doc.get("text") or doc.get("description") or "")[:280]
        snippet = text.replace("\n", " ").strip()
        lines.append(f"{i}. {title}: {snippet}")
    return "\n".join(lines)


def _build_user_prompt(
    barriers: list[str], deterministic_steps: list[str], docs: list[dict],
) -> str:
    return (
        f"Resident's primary barriers: "
        f"{', '.join(barriers) if barriers else '(none disclosed)'}\n\n"
        f"Deterministic baseline steps (use as factual anchor):\n"
        + "\n".join(f"- {s}" for s in deterministic_steps[:6])
        + "\n\n"
        + f"Retrieved Fort Worth resources:\n{_format_docs(docs)}\n\n"
        + f"Write exactly {_MAX_STEPS} Monday-morning steps. Each step "
        + "should reference a real Fort Worth resource from the retrieved "
        + "context or the baseline. Order them by what to do FIRST."
    )


def _parse_steps(text: str) -> list[str]:
    """Parse Haiku output into a clean list of step strings."""
    raw_lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    cleaned: list[str] = []
    for line in raw_lines:
        # Strip leading numbering/bullet markers
        stripped = re.sub(r"^[\-\*\d\.\)\s]+", "", line).strip()
        if stripped and len(stripped) > 10:
            cleaned.append(stripped)
    return cleaned[:_MAX_STEPS]


def _validate_grounding(steps: list[str], deterministic: list[str], docs: list[dict]) -> bool:
    """Reject Haiku output that hallucinates resources not in our context.

    A step is GROUNDED if it mentions any noun phrase from either the
    deterministic baseline or a retrieved doc title.  At least 2 of 4
    steps must be grounded — else we fall back.
    """
    anchors: set[str] = set()
    for s in deterministic:
        for word in s.split():
            if len(word) > 5 and word[0].isupper():
                anchors.add(word.strip(".,()").lower())
    for d in docs:
        title = d.get("title") or d.get("name") or ""
        for word in title.split():
            if len(word) > 5 and word[0].isupper():
                anchors.add(word.strip(".,()").lower())
    # Always allow Workforce/Trinity/TWC anchors as canonical FW vocab
    anchors.update({"workforce", "trinity", "metro", "twc", "fort", "worth", "tarrant"})

    grounded = 0
    for s in steps:
        words = {w.strip(".,()").lower() for w in s.split()}
        if anchors & words:
            grounded += 1
    return grounded >= 2


async def compose_next_steps(
    *,
    session_id: str,
    barriers: list[str],
    deterministic_steps: list[str],
    retrieved_docs: list[dict[str, Any]],
) -> dict:
    """Return ``{"steps": list[str], "source": "haiku"|"fallback", "cached": bool}``.

    Always returns 1+ step.  Falls back to deterministic_steps on any
    Haiku error or if grounding validation rejects the output.
    """
    cached = next_step_cache.get(session_id)
    if cached is not None:
        return {"steps": cached, "source": "haiku", "cached": True}

    user_prompt = _build_user_prompt(barriers, deterministic_steps, retrieved_docs)
    try:
        result = await call_haiku(_SYSTEM_PROMPT, user_prompt, max_tokens=_MAX_TOKENS)
    except HaikuError as exc:
        logger.warning("next_step_composer falling back: %s", exc)
        return {"steps": deterministic_steps[:_MAX_STEPS], "source": "fallback", "cached": False}

    steps = _parse_steps(result.text)
    if len(steps) < 2 or not _validate_grounding(steps, deterministic_steps, retrieved_docs):
        logger.warning("next_step_composer rejected Haiku output (grounding/parse)")
        return {"steps": deterministic_steps[:_MAX_STEPS], "source": "fallback", "cached": False}

    next_step_cache.set(session_id, steps)
    logger.info(
        "next_step_composer haiku ok session=%s tokens_in=%d tokens_out=%d cost~$%.4f",
        session_id, result.input_tokens, result.output_tokens,
        result.estimated_cost_usd,
    )
    return {"steps": steps, "source": "haiku", "cached": False}

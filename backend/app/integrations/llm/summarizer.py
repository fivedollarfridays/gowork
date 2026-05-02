"""Haiku-augmented job description summarizer.

Job listings (USAJobs / Adzuna / HonestJobs) often have 1500+ char
descriptions.  Surfacing those raw in JobMatchCard buries the user.
This module compresses each to:
- 2-sentence pitch
- 3-bullet "what you'd do"

Cache: keyed by hash of description + cache_version (90d TTL).
Fallback: first 200 chars of original on any LLM error / parse failure.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re

from app.integrations.llm._cache import job_summary_cache
from app.integrations.llm._haiku_client import HaikuError, call_haiku

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are a workforce navigator helping Fort Worth residents quickly "
    "evaluate job listings. Given a raw job description, output ONLY a "
    "JSON object with this exact schema and nothing else:\n"
    '{"pitch": "<2 sentences, direct, no marketing fluff>", '
    '"duties": ["<bullet 1>", "<bullet 2>", "<bullet 3>"]}\n'
    "RULES: Each bullet starts with a verb. Do not invent benefits, "
    "wages, or schedule details that weren't in the description. If the "
    "description is sparse, leave duties shorter rather than fabricate. "
    "Output JSON ONLY — no preamble, no code fences."
)

_MAX_TOKENS = 350
_CACHE_VERSION = "v1"


def _description_hash(description: str) -> str:
    digest = hashlib.sha256(description.encode("utf-8", errors="ignore")).hexdigest()[:16]
    return f"{_CACHE_VERSION}|{digest}"


def _build_user_prompt(title: str, description: str) -> str:
    truncated = description[:3000]
    return (
        f"Job title: {title or '(unknown)'}\n\n"
        f"Description:\n{truncated}\n\n"
        "Return JSON exactly as specified."
    )


def _strip_code_fences(text: str) -> str:
    """Remove ```json ... ``` fences if Haiku ignores instructions."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        # Drop the first fence line, then drop trailing ```
        cleaned = re.sub(r"^```(?:json)?\s*\n", "", cleaned)
        cleaned = re.sub(r"\n```\s*$", "", cleaned)
    return cleaned.strip()


def _parse_haiku_response(text: str) -> dict:
    """Parse Haiku JSON or raise ValueError."""
    cleaned = _strip_code_fences(text)
    parsed = json.loads(cleaned)
    if not isinstance(parsed, dict):
        raise ValueError("not a dict")
    pitch = parsed.get("pitch", "").strip()
    duties_raw = parsed.get("duties", [])
    duties = [str(d).strip() for d in duties_raw if str(d).strip()][:3]
    if not pitch or len(pitch) < 10:
        raise ValueError("pitch too short")
    return {"pitch": pitch, "duties": duties}


def _fallback_summary(title: str, description: str) -> dict:
    """Deterministic fallback — first sentence + first 200 chars."""
    if not description:
        return {"pitch": title or "Job listing", "duties": []}
    snippet = description.strip()[:200]
    if "." in snippet:
        first_sentence = snippet.split(".")[0] + "."
    else:
        first_sentence = snippet
    return {"pitch": first_sentence, "duties": []}


def _fallback_response(title: str, description: str) -> dict:
    out = _fallback_summary(title, description)
    out["source"] = "fallback"
    out["cached"] = False
    return out


async def _try_summarize(title: str, description: str) -> dict | None:
    """Run Haiku + parse. Return parsed summary or None on any error."""
    try:
        result = await call_haiku(
            _SYSTEM_PROMPT, _build_user_prompt(title, description),
            max_tokens=_MAX_TOKENS,
        )
        summary = _parse_haiku_response(result.text)
    except HaikuError as exc:
        logger.warning("summarizer falling back: %s", exc)
        return None
    except (ValueError, json.JSONDecodeError) as exc:
        logger.warning("summarizer parse failed: %s", exc)
        return None
    logger.info(
        "summarizer haiku ok title=%r tokens_in=%d tokens_out=%d cost~$%.4f",
        title[:40], result.input_tokens, result.output_tokens,
        result.estimated_cost_usd,
    )
    return summary


async def summarize_job(*, title: str, description: str) -> dict:
    """Return ``{"pitch": str, "duties": list[str], "source": "haiku"|"fallback", "cached": bool}``.

    Always returns a dict.  Cache hits return immediately.  Cache key is a
    hash of the description, so identical postings across sources share
    the same cache slot.
    """
    if not description or len(description.strip()) < 30:
        return _fallback_response(title, description)

    key = _description_hash(description)
    cached = job_summary_cache.get(key)
    if cached is not None:
        return {**cached, "source": "haiku", "cached": True}

    summary = await _try_summarize(title, description)
    if summary is None:
        return _fallback_response(title, description)

    job_summary_cache.set(key, summary)
    return {**summary, "source": "haiku", "cached": False}

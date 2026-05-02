"""Two-stage Spanish resume polish — dict first, Haiku for the residual.

A Spanish-speaking applicant submitting a Spanish resume gets a poor
match because the scorer's keyword taxonomy is English-only. This module
returns an English-projected version of the resume so the existing
relevance_scorer can run unchanged.

Stage 1: deterministic dict translation (free, fast, exhaustive for the
common occupational vocabulary — enfermería, montacargas, soldadura).

Stage 2: Haiku polish for tokens the dict missed.  Only invoked if more
than 30% of the resume bytes remain unrecognized after stage 1.

Cache: 7d TTL keyed by hash of source.  Polishing the same resume twice
costs nothing the second time.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re

from app.integrations.llm._cache import spanish_polish_cache
from app.integrations.llm._haiku_client import HaikuError, call_haiku
from app.integrations.llm._spanish_dict import SPANISH_ENGLISH, SPANISH_STOPWORDS

logger = logging.getLogger(__name__)

_CACHE_VERSION = "v1"


def _detect_spanish(text: str) -> bool:
    """Heuristic: Spanish stopword density above ~3%."""
    if not text or len(text) < 30:
        return False
    words = re.findall(r"[a-záéíóúñ]+", text.lower())
    if not words:
        return False
    sp_hits = sum(1 for w in words if w in SPANISH_STOPWORDS)
    return (sp_hits / len(words)) > 0.03


def _dict_translate(text: str) -> tuple[str, list[str]]:
    """Apply dict translation. Returns (translated_text, residual_unknowns)."""
    out = text
    # Sort longest first so multi-word phrases match before single words
    for sp_phrase in sorted(SPANISH_ENGLISH, key=len, reverse=True):
        en = SPANISH_ENGLISH[sp_phrase]
        out = re.sub(
            rf"\b{re.escape(sp_phrase)}\b", en, out, flags=re.IGNORECASE,
        )
    residual = re.findall(r"\b[a-z]*[áéíóúñ][a-záéíóúñ]+\b", out, flags=re.IGNORECASE)
    return out, residual


def _residual_ratio(translated: str, residual: list[str]) -> float:
    if not translated:
        return 0.0
    residual_chars = sum(len(r) for r in residual)
    return residual_chars / max(len(translated), 1)


def _hash_text(text: str) -> str:
    digest = hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()[:16]
    return f"{_CACHE_VERSION}|{digest}"


_HAIKU_SYSTEM = (
    "You are translating a Spanish-language resume into English so a "
    "keyword-based job matching system can score it. Preserve job titles, "
    "skills, certifications, and years of experience. Do not invent "
    "qualifications. Output ONLY the English translation, no preamble, "
    "no notes, no markdown."
)


async def _haiku_polish(text_so_far: str, residual: list[str]) -> str | None:
    """Ask Haiku to translate the residual unknown spans.

    We pass the WHOLE text (not just residual fragments) so Haiku has
    context.  Returns the polished English text, or None on error.
    """
    user = (
        f"Spanish source resume:\n{text_so_far[:3000]}\n\n"
        f"Tokens still untranslated (need attention): "
        f"{', '.join(residual[:30])}\n\n"
        "Output the full resume in English."
    )
    try:
        result = await call_haiku(_HAIKU_SYSTEM, user, max_tokens=900)
    except HaikuError as exc:
        logger.warning("spanish_polish haiku failed: %s", exc)
        return None
    cleaned = result.text.strip()
    return cleaned or None


async def polish_spanish_resume(text: str) -> dict:
    """Return ``{"english_text": str, "stage": "dict"|"haiku"|"passthrough", "cached": bool}``.

    Always returns a dict; never raises.  ``stage`` is "passthrough" when
    the input doesn't look Spanish at all.
    """
    if not text or not text.strip():
        return {"english_text": text, "stage": "passthrough", "cached": False}

    if not _detect_spanish(text):
        return {"english_text": text, "stage": "passthrough", "cached": False}

    key = _hash_text(text)
    cached = spanish_polish_cache.get(key)
    if cached is not None:
        return {**cached, "cached": True}

    dict_translated, residual = _dict_translate(text)
    ratio = _residual_ratio(dict_translated, residual)

    if ratio < 0.30:
        out = {"english_text": dict_translated, "stage": "dict", "cached": False}
        spanish_polish_cache.set(key, {k: v for k, v in out.items() if k != "cached"})
        return out

    polished = await _haiku_polish(dict_translated, residual)
    if polished is None:
        # Haiku failed -- still return dict-translated (better than raw Spanish)
        return {"english_text": dict_translated, "stage": "dict", "cached": False}

    out = {"english_text": polished, "stage": "haiku", "cached": False}
    spanish_polish_cache.set(key, {k: v for k, v in out.items() if k != "cached"})
    return out

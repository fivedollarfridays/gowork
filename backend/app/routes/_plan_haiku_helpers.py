"""Helpers for the Haiku-augmented plan endpoints.

Extracted to keep ``plan_haiku.py`` under the file-size warning threshold.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import HTTPException, Request

logger = logging.getLogger(__name__)


def safe_parse(raw: Any, default: Any) -> Any:
    """Parse JSON string, return default on any error."""
    if not raw:
        return default
    if isinstance(raw, (list, dict)):
        return raw
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return default


def flat_matches(plan_data: dict) -> list[dict]:
    """Concatenate strong + possible + after_repair into one ordered list."""
    if not plan_data:
        return []
    return (
        list(plan_data.get("strong_matches") or [])
        + list(plan_data.get("possible_matches") or [])
        + list(plan_data.get("after_repair") or [])
    )


def retrieve_docs_for_session(request: Request, barriers: list[str]) -> list[dict]:
    """Pull top RAG docs filtered by the user's barriers.

    Falls back gracefully if the RAG store isn't ready (early lifespan,
    test harness with no FAISS).
    """
    store = getattr(request.app.state, "rag_store", None)
    if store is None or not getattr(store, "is_ready", lambda: False)():
        return []
    query = (
        f"Resources for Fort Worth resident with barriers: "
        f"{', '.join(barriers) if barriers else 'general employment'}"
    )
    try:
        return store.search(query, n=3, barrier_filter=barriers or None)
    except (RuntimeError, ValueError, OSError):
        logger.warning("RAG search failed in match explainer", exc_info=True)
        return []


def resolve_job_or_raise(plan_data: dict, job_index: int) -> dict:
    """Look up the job by flat index or raise the right HTTPException."""
    matches = flat_matches(plan_data)
    if not matches:
        raise HTTPException(status_code=400, detail="No job matches in this plan")
    if job_index >= len(matches):
        raise HTTPException(status_code=404, detail="Job index out of range")
    return matches[job_index]

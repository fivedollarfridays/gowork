"""Haiku-augmented plan endpoints (Agent-2 Stage 3).

Endpoints:
- POST /api/plan/{session_id}/match/{job_index}/explain
  Returns a Haiku-composed "Explain My Match" narrative with deterministic
  fallback when the LLM is unavailable.

The job is identified by its index in the bucketed plan (strong/possible/
after_repair flat list) so we don't depend on listing IDs.
"""

from __future__ import annotations

import json
import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import audit_log, get_client_ip
from app.core.auth import require_session_token
from app.core.database import get_db
from app.core.queries import get_session_by_id
from app.integrations.llm.match_explainer import explain_match

logger = logging.getLogger(__name__)

_UUID_RE = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
SessionId = Annotated[str, Path(pattern=_UUID_RE)]
JobIndex = Annotated[int, Path(ge=0, le=99)]

router = APIRouter(prefix="/api/plan", tags=["plan_haiku"])


def _safe_parse(raw: Any, default: Any) -> Any:
    """Parse JSON string, return default on any error."""
    if not raw:
        return default
    if isinstance(raw, (list, dict)):
        return raw
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return default


def _flat_matches(plan_data: dict) -> list[dict]:
    """Concatenate strong + possible + after_repair into one ordered list."""
    if not plan_data:
        return []
    return (
        list(plan_data.get("strong_matches") or [])
        + list(plan_data.get("possible_matches") or [])
        + list(plan_data.get("after_repair") or [])
    )


def _retrieve_docs_for_session(request: Request, barriers: list[str]) -> list[dict]:
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


def _resolve_job_or_raise(plan_data: dict, job_index: int) -> dict:
    """Look up the job by flat index or raise the right HTTPException."""
    matches = _flat_matches(plan_data)
    if not matches:
        raise HTTPException(status_code=400, detail="No job matches in this plan")
    if job_index >= len(matches):
        raise HTTPException(status_code=404, detail="Job index out of range")
    return matches[job_index]


@router.post("/{session_id}/match/{job_index}/explain")
async def explain_job_match(
    session_id: SessionId,
    job_index: JobIndex,
    request: Request,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Compose a Haiku-augmented explanation for one job match.

    Returns ``{"text": str, "source": "haiku"|"fallback", "cached": bool,
    "job_index": int}``.
    """
    await require_session_token(db, session_id, token)
    row = await get_session_by_id(db, session_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Session not found")

    plan_data = _safe_parse(row.get("plan"), {})
    job = _resolve_job_or_raise(plan_data, job_index)
    barriers = _safe_parse(row.get("barriers"), [])

    out = await explain_match(
        session_id=session_id,
        job=job,
        score_breakdown=job.get("score_breakdown"),
        barriers=barriers,
        retrieved_docs=_retrieve_docs_for_session(request, barriers),
    )
    out["job_index"] = job_index

    audit_log(
        "match_explained", session_id=session_id,
        client_ip=get_client_ip(request),
        job_index=job_index, source=out["source"], cached=out["cached"],
    )
    return out

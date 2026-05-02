"""Haiku-augmented plan endpoints (Agent-2 Stage 3).

Endpoints:
- POST /api/plan/{session_id}/match/{job_index}/explain
  Haiku-composed "Explain My Match" narrative.
- POST /api/plan/{session_id}/next-steps/compose
  Haiku-composed Monday-morning action sequence, RAG-grounded.

Both fall back to deterministic output when the LLM is unavailable.
The canonical plan in the DB is NOT mutated by either endpoint.
"""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import audit_log, get_client_ip
from app.core.auth import require_session_token
from app.core.database import get_db
from app.core.queries import get_session_by_id
from app.integrations.llm.match_explainer import explain_match
from app.integrations.llm.next_step_composer import compose_next_steps
from app.routes._plan_haiku_helpers import (
    resolve_job_or_raise,
    retrieve_docs_for_session,
    safe_parse,
)

logger = logging.getLogger(__name__)

_UUID_RE = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
SessionId = Annotated[str, Path(pattern=_UUID_RE)]
JobIndex = Annotated[int, Path(ge=0, le=99)]

router = APIRouter(prefix="/api/plan", tags=["plan_haiku"])


@router.post("/{session_id}/match/{job_index}/explain")
async def explain_job_match(
    session_id: SessionId,
    job_index: JobIndex,
    request: Request,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Compose a Haiku-augmented explanation for one job match."""
    await require_session_token(db, session_id, token)
    row = await get_session_by_id(db, session_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Session not found")

    plan_data = safe_parse(row.get("plan"), {})
    job = resolve_job_or_raise(plan_data, job_index)
    barriers = safe_parse(row.get("barriers"), [])

    out = await explain_match(
        session_id=session_id,
        job=job,
        score_breakdown=job.get("score_breakdown"),
        barriers=barriers,
        retrieved_docs=retrieve_docs_for_session(request, barriers),
    )
    out["job_index"] = job_index
    audit_log(
        "match_explained", session_id=session_id,
        client_ip=get_client_ip(request),
        job_index=job_index, source=out["source"], cached=out["cached"],
    )
    return out


@router.post("/{session_id}/next-steps/compose")
async def compose_next_step_plan(
    session_id: SessionId,
    request: Request,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Replace ``immediate_next_steps`` with a Haiku-composed Monday sequence."""
    await require_session_token(db, session_id, token)
    row = await get_session_by_id(db, session_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Session not found")

    plan_data = safe_parse(row.get("plan"), {})
    deterministic = list(plan_data.get("immediate_next_steps") or [])
    if not deterministic:
        raise HTTPException(
            status_code=400, detail="No deterministic next steps in plan",
        )
    barriers = safe_parse(row.get("barriers"), [])
    out = await compose_next_steps(
        session_id=session_id,
        barriers=barriers,
        deterministic_steps=deterministic,
        retrieved_docs=retrieve_docs_for_session(request, barriers),
    )
    audit_log(
        "next_steps_composed", session_id=session_id,
        client_ip=get_client_ip(request),
        source=out["source"], cached=out["cached"],
    )
    return out

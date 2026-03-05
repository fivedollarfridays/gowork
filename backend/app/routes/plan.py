"""GET/POST /api/plan — session plan lookup and AI narrative generation."""

import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.client import build_fallback_narrative, generate_narrative
from app.core.database import get_db
from app.core.queries import get_session_by_id, update_session_plan

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/plan", tags=["plan"])


@router.get("/{session_id}")
async def get_plan(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Look up session and return existing plan, or 404."""
    row = await get_session_by_id(db, session_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        plan = json.loads(row["plan"]) if row["plan"] else None
        barriers = json.loads(row["barriers"]) if row["barriers"] else []
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Corrupt session data")
    return {
        "session_id": session_id,
        "barriers": barriers,
        "qualifications": row.get("qualifications"),
        "plan": plan,
    }


@router.post("/{session_id}/generate")
async def generate_plan_narrative(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Generate AI narrative for an existing plan. Falls back to template."""
    row = await get_session_by_id(db, session_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Session not found")

    if not row["plan"]:
        raise HTTPException(status_code=400, detail="No plan exists for this session. Run assessment first.")

    try:
        barriers = json.loads(row["barriers"])
        plan_data = json.loads(row["plan"])
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Corrupt session data")
    qualifications = row.get("qualifications", "")

    try:
        narrative = await generate_narrative(
            barriers=barriers,
            qualifications=qualifications,
            plan_data=plan_data,
        )
    except Exception:
        logger.warning("Claude API unavailable, using fallback", exc_info=True)
        narrative = build_fallback_narrative(
            barriers=barriers,
            qualifications=qualifications,
            plan_data=plan_data,
        )

    await update_session_plan(
        db,
        session_id,
        json.dumps({**plan_data, "resident_summary": narrative.summary}),
    )

    return narrative.model_dump()

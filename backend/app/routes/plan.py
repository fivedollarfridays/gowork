"""GET/POST /api/plan — session plan lookup, AI narrative, and plan refresh."""

import json
import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.client import build_fallback_narrative, generate_narrative
from app.core.audit import audit_log, get_client_ip
from app.core.auth import require_session_token
from app.core.database import get_db
from app.core.queries import get_session_by_id, update_session_plan
from app.core.rate_limit import RateLimiter, require_rate_limit
from app.modules.matching.engine import generate_plan
from app.modules.matching.types import UserProfile

logger = logging.getLogger(__name__)

_UUID_RE = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
SessionId = Annotated[str, Path(pattern=_UUID_RE)]

router = APIRouter(prefix="/api/plan", tags=["plan"])

_rate_limiter = RateLimiter(max_requests=5, window_seconds=60)
_check_rate = require_rate_limit(_rate_limiter)


async def _fetch_session(db: AsyncSession, session_id: str, token: str) -> dict:
    """Validate token, fetch session row, or raise 404."""
    await require_session_token(db, session_id, token)
    row = await get_session_by_id(db, session_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return row


def _safe_json(raw: str | None, default: Any = None) -> Any:
    """Parse a JSON string, raising 500 on corrupt data."""
    if not raw:
        return default
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Corrupt session data")


@router.get("/{session_id}")
async def get_plan(
    session_id: SessionId,
    request: Request,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Look up session and return existing plan, or 404."""
    row = await _fetch_session(db, session_id, token)
    audit_log("plan_accessed", session_id=session_id, client_ip=get_client_ip(request))

    plan = _safe_json(row["plan"])
    barriers = _safe_json(row["barriers"], [])
    credit_profile = _safe_json(row.get("credit_profile"))
    return {
        "session_id": session_id,
        "barriers": barriers,
        "qualifications": row.get("qualifications"),
        "plan": plan,
        "credit_profile": credit_profile,
    }


@router.post("/{session_id}/generate")
async def generate_plan_narrative(
    session_id: SessionId,
    request: Request,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(_check_rate),
) -> dict:
    """Generate AI narrative for an existing plan. Falls back to template."""
    row = await _fetch_session(db, session_id, token)
    if not row["plan"]:
        raise HTTPException(status_code=400, detail="No plan exists for this session. Run assessment first.")
    barriers = _safe_json(row["barriers"], [])
    plan_data = _safe_json(row["plan"])
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

    await update_session_plan(db, session_id, json.dumps({**plan_data, "resident_summary": narrative.summary}))

    audit_log("plan_generated", session_id=session_id, client_ip=get_client_ip(request))
    return narrative.model_dump()


@router.post("/{session_id}/refresh")
async def refresh_plan(
    session_id: SessionId,
    request: Request,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(_check_rate),
) -> dict:
    """Re-run the matching pipeline with stored profile data."""
    row = await _fetch_session(db, session_id, token)

    profile_json = row.get("profile")
    if not profile_json:
        raise HTTPException(status_code=400, detail="No profile stored. Re-run the assessment.")

    try:
        profile = UserProfile(**json.loads(profile_json))
    except (json.JSONDecodeError, ValueError):
        raise HTTPException(status_code=400, detail="Stored profile is corrupt. Re-run the assessment.")

    credit_result = _safe_json(row.get("credit_profile"))

    new_plan = await generate_plan(
        profile, db,
        resume_text=row.get("qualifications", ""),
        credit_result=credit_result,
    )
    await update_session_plan(db, session_id, json.dumps(new_plan.model_dump()))

    audit_log("plan_refreshed", session_id=session_id, client_ip=get_client_ip(request))

    return {
        "session_id": session_id,
        "barriers": _safe_json(row["barriers"], []),
        "qualifications": row.get("qualifications"),
        "plan": new_plan.model_dump(),
        "credit_profile": credit_result,
    }

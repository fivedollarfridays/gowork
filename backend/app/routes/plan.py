"""GET/POST /api/plan — session plan lookup, AI narrative, and career center package."""

import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.client import build_fallback_narrative, generate_narrative
from app.core.database import get_db
from app.core.queries import get_session_by_id, update_session_plan
from app.modules.credit.types import CreditAssessmentResult
from app.modules.matching.career_center_package import assemble_package
from app.modules.matching.types import (
    BarrierType,
    EmploymentStatus,
    ReEntryPlan,
    UserProfile,
)
from app.modules.matching.wioa_screener import screen_wioa_eligibility
from app.routes.assessment import determine_severity

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


@router.get("/{session_id}/career-center")
async def get_career_center_package(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Build and return a Career Center Ready Package for this session."""
    row = await get_session_by_id(db, session_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if not row["plan"]:
        raise HTTPException(status_code=404, detail="No plan for session")

    try:
        barrier_names = json.loads(row["barriers"]) if row["barriers"] else []
        plan_data = json.loads(row["plan"])
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Corrupt session data")

    valid_values = {bt.value for bt in BarrierType}
    barrier_types = [BarrierType(b) for b in barrier_names if b in valid_values]

    if row.get("profile"):
        try:
            profile = UserProfile(**json.loads(row["profile"]))
        except (json.JSONDecodeError, ValueError):
            profile = _build_profile_from_session(session_id, barrier_types, row)
    else:
        profile = _build_profile_from_session(session_id, barrier_types, row)

    plan = ReEntryPlan(**plan_data)
    wioa = plan.wioa_eligibility or screen_wioa_eligibility(profile)

    credit_result = None
    if row.get("credit_profile"):
        try:
            credit_result = CreditAssessmentResult(**json.loads(row["credit_profile"]))
        except (json.JSONDecodeError, ValueError):
            logger.warning("Invalid credit profile data for %s", session_id)

    package = assemble_package(profile, plan, wioa, credit_result)
    return package.model_dump()


def _build_profile_from_session(
    session_id: str,
    barriers: list[BarrierType],
    row: dict,
) -> UserProfile:
    """Reconstruct a UserProfile from stored session data."""
    return UserProfile(
        session_id=session_id,
        zip_code="36104",
        employment_status=EmploymentStatus.UNEMPLOYED,
        barrier_count=len(barriers),
        primary_barriers=barriers,
        barrier_severity=determine_severity(len(barriers)),
        needs_credit_assessment=BarrierType.CREDIT in barriers,
        transit_dependent=BarrierType.TRANSPORTATION in barriers,
        schedule_type="daytime",
        work_history=row.get("qualifications", ""),
        target_industries=[],
    )

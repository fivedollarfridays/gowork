"""GET /api/plan/{session_id}/career-center — Career Center Ready Package."""

import json
import logging

from fastapi import Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.credit.types import CreditAssessmentResult
from app.modules.matching.career_center_package import assemble_package
from app.modules.matching.types import (
    AvailableHours,
    BarrierType,
    EmploymentStatus,
    ReEntryPlan,
    UserProfile,
    determine_severity,
)
from app.modules.matching.wioa_screener import screen_wioa_eligibility
from app.routes.plan import SessionId, _fetch_session, _safe_json, router

logger = logging.getLogger(__name__)


@router.get("/{session_id}/career-center")
async def get_career_center_package(
    session_id: SessionId,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Build and return a Career Center Ready Package for this session."""
    row = await _fetch_session(db, session_id, token)
    if not row["plan"]:
        raise HTTPException(status_code=404, detail="No plan for session")

    barrier_names = _safe_json(row["barriers"], [])
    plan_data = _safe_json(row["plan"])

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
    """Reconstruct a UserProfile from stored session data (fallback defaults)."""
    logger.warning("Using fallback profile for session %s (stored profile missing/corrupt)", session_id)
    return UserProfile(
        session_id=session_id,
        zip_code="36104",
        employment_status=EmploymentStatus.UNEMPLOYED,
        barrier_count=len(barriers),
        primary_barriers=barriers,
        barrier_severity=determine_severity(len(barriers)),
        needs_credit_assessment=BarrierType.CREDIT in barriers,
        transit_dependent=BarrierType.TRANSPORTATION in barriers,
        schedule_type=AvailableHours.DAYTIME,
        work_history=row.get("qualifications", ""),
        target_industries=[],
    )

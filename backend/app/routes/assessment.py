"""POST /api/assessment — intake assessment and matching pipeline."""

import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import audit_log, get_client_ip
from app.core.database import get_db
from app.core.queries import create_session, insert_record_profile, update_session_plan
from app.core.queries_feedback import create_feedback_token
from app.core.rate_limit import RateLimiter, require_rate_limit
from app.modules.matching.engine import generate_plan
from app.modules.matching.types import (
    AssessmentRequest,
    BarrierType,
    UserProfile,
    determine_severity,
)

router = APIRouter(prefix="/api/assessment", tags=["assessment"])

_rate_limiter = RateLimiter(max_requests=10, window_seconds=60)
_check_rate = require_rate_limit(_rate_limiter)


def extract_primary_barriers(barriers: dict[BarrierType, bool]) -> list[BarrierType]:
    """Return list of BarrierType enums for checked barriers."""
    return [bt for bt, checked in barriers.items() if checked]


def _build_profile(session_id: str, request: AssessmentRequest) -> UserProfile:
    """Build UserProfile from assessment request."""
    primary_barriers = extract_primary_barriers(request.barriers)
    return UserProfile(
        session_id=session_id,
        zip_code=request.zip_code,
        employment_status=request.employment_status,
        barrier_count=len(primary_barriers),
        primary_barriers=primary_barriers,
        barrier_severity=determine_severity(len(primary_barriers)),
        needs_credit_assessment=request.barriers.get(BarrierType.CREDIT, False),
        transit_dependent=(
            not request.has_vehicle
            and request.barriers.get(BarrierType.TRANSPORTATION, False)
        ),
        schedule_type=request.schedule_constraints.available_hours,
        work_history=request.work_history,
        target_industries=request.target_industries,
        record_profile=request.record_profile,
    )


@router.post("/", status_code=201)
async def create_assessment(
    request: AssessmentRequest,
    raw_request: Request,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(_check_rate),
) -> dict:
    """Receive barrier form, create session, run matching, return results."""
    session_id = str(uuid.uuid4())
    profile = _build_profile(session_id, request)

    await create_session(db, {
        "barriers": json.dumps([b.value for b in profile.primary_barriers]),
        "credit_profile": request.credit_result.model_dump_json() if request.credit_result else None,
        "qualifications": request.work_history,
        "plan": None,
        "profile": json.dumps(profile.model_dump()),
    }, session_id=session_id)

    if request.record_profile:
        await insert_record_profile(db, session_id, request.record_profile)

    plan = await generate_plan(
        profile, db,
        resume_text=request.resume_text,
        credit_result=request.credit_result.model_dump() if request.credit_result else None,
    )

    await update_session_plan(db, session_id, json.dumps(plan.model_dump()))

    feedback_token = await create_feedback_token(db, session_id)

    audit_log("session_created", session_id=session_id, client_ip=get_client_ip(raw_request),
              barriers=len(profile.primary_barriers))

    return {
        "session_id": session_id,
        "profile": profile.model_dump(),
        "plan": plan.model_dump(),
        "feedback_token": feedback_token,
    }

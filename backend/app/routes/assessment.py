"""POST /api/assessment — intake assessment and matching pipeline."""

import json
import time
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.queries import create_session, update_session_plan
from app.core.queries_feedback import create_feedback_token
from app.modules.matching.engine import generate_plan
from app.modules.matching.types import (
    AssessmentRequest,
    BarrierSeverity,
    BarrierType,
    UserProfile,
)

router = APIRouter(prefix="/api/assessment", tags=["assessment"])


class _RateLimiter:
    """Simple in-memory rate limiter: max_requests per window_seconds per key."""

    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self._max = max_requests
        self._window = window_seconds
        self._requests: dict[str, list[float]] = {}

    def check(self, key: str) -> bool:
        """Return True if under limit, False if over."""
        now = time.monotonic()
        cutoff = now - self._window
        timestamps = self._requests.get(key, [])
        timestamps = [t for t in timestamps if t > cutoff]
        if len(timestamps) >= self._max:
            self._requests[key] = timestamps
            return False
        timestamps.append(now)
        self._requests[key] = timestamps
        return True

    def clear(self) -> None:
        """Reset all tracked requests (for testing)."""
        self._requests.clear()


_rate_limiter = _RateLimiter()


def determine_severity(barrier_count: int) -> BarrierSeverity:
    """3+ barriers = HIGH, 2 = MEDIUM, 1 or 0 = LOW."""
    if barrier_count >= 3:
        return BarrierSeverity.HIGH
    if barrier_count == 2:
        return BarrierSeverity.MEDIUM
    return BarrierSeverity.LOW


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
        schedule_type=request.schedule_constraints.available_hours.value,
        work_history=request.work_history,
        target_industries=request.target_industries,
    )


@router.post("/", status_code=201)
async def create_assessment(
    request: AssessmentRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Receive barrier form, create session, run matching, return results."""
    client_ip = http_request.client.host if http_request.client else "unknown"
    if not _rate_limiter.check(client_ip):
        raise HTTPException(status_code=429, detail="Too many requests. Please try again later.")
    session_id = str(uuid.uuid4())
    profile = _build_profile(session_id, request)

    await create_session(db, {
        "barriers": json.dumps([b.value for b in profile.primary_barriers]),
        "credit_profile": None,
        "qualifications": request.work_history,
        "plan": None,
    }, session_id=session_id)

    plan = await generate_plan(profile, db)

    await update_session_plan(db, session_id, json.dumps(plan.model_dump()))

    feedback_token = await create_feedback_token(db, session_id)

    return {
        "session_id": session_id,
        "profile": profile.model_dump(),
        "plan": plan.model_dump(),
        "feedback_token": feedback_token,
    }

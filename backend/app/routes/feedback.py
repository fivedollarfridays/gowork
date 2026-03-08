"""Feedback routes — resource and visit feedback endpoints."""

import json

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import audit_log, get_client_ip
from app.core.auth import require_session_token
from app.core.database import get_db
from app.core.queries_feedback import (
    has_visit_feedback,
    insert_resource_feedback,
    insert_visit_feedback,
    token_exists,
    validate_token,
)
from app.core.rate_limit import RateLimiter, require_rate_limit
from app.modules.feedback.types import (
    ResourceFeedbackRequest,
    ResourceFeedbackResponse,
    VisitFeedbackRequest,
    VisitFeedbackResponse,
)

router = APIRouter(prefix="/api/feedback", tags=["feedback"])

_rate_limiter = RateLimiter(max_requests=20, window_seconds=60)
_check_rate = require_rate_limit(_rate_limiter)


async def _require_valid_token(db: AsyncSession, token: str) -> str:
    """Validate token, raising 410 (expired) or 404 (unknown) on failure."""
    result = await validate_token(db, token)
    if result:
        return result
    if await token_exists(db, token):
        raise HTTPException(status_code=410, detail="Token expired")
    raise HTTPException(status_code=404, detail="Token not found")


@router.post("/resource", response_model=ResourceFeedbackResponse)
async def submit_resource_feedback(
    feedback: ResourceFeedbackRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(_check_rate),
) -> ResourceFeedbackResponse:
    """Record whether a resource was helpful. One vote per resource per session."""
    await require_session_token(db, feedback.session_id, feedback.token)

    await insert_resource_feedback(db, feedback)

    audit_log("feedback_resource", session_id=feedback.session_id, client_ip=get_client_ip(request),
              resource_id=feedback.resource_id, helpful=feedback.helpful)

    return ResourceFeedbackResponse(
        success=True,
        resource_id=feedback.resource_id,
        helpful=feedback.helpful,
    )


@router.get("/validate/{token}")
async def validate_feedback_token(
    token: str,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(_check_rate),
) -> dict:
    """Validate a feedback token. Returns 200 if valid, 410 if expired, 404 if unknown."""
    await _require_valid_token(db, token)
    return {"valid": True}


@router.post("/visit", response_model=VisitFeedbackResponse)
async def submit_visit_feedback(
    feedback: VisitFeedbackRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(_check_rate),
) -> VisitFeedbackResponse:
    """Record visit feedback. One submission per session."""
    session_id = await _require_valid_token(db, feedback.token)

    if await has_visit_feedback(db, session_id):
        raise HTTPException(status_code=409, detail="Feedback already submitted")

    await insert_visit_feedback(
        db,
        session_id=session_id,
        made_it_to_center=feedback.made_it_to_center,
        outcomes_json=json.dumps(feedback.outcomes),
        plan_accuracy=feedback.plan_accuracy,
        free_text=feedback.free_text,
    )

    audit_log("feedback_visit", session_id=session_id, client_ip=get_client_ip(request))

    return VisitFeedbackResponse(success=True)

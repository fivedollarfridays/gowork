"""Feedback routes — resource and visit feedback endpoints."""

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.queries_feedback import (
    has_visit_feedback,
    insert_resource_feedback,
    insert_visit_feedback,
    session_exists,
    token_exists,
    validate_token,
)
from app.modules.feedback.types import (
    ResourceFeedbackRequest,
    ResourceFeedbackResponse,
    VisitFeedbackRequest,
    VisitFeedbackResponse,
)

router = APIRouter(prefix="/api/feedback", tags=["feedback"])


async def _require_valid_token(db: AsyncSession, token: str) -> str:
    """Validate token, raising 410 (expired) or 404 (unknown) on failure."""
    session_id = await validate_token(db, token)
    if session_id:
        return session_id
    if await token_exists(db, token):
        raise HTTPException(status_code=410, detail="Token expired")
    raise HTTPException(status_code=404, detail="Token not found")


@router.post("/resource", response_model=ResourceFeedbackResponse)
async def submit_resource_feedback(
    feedback: ResourceFeedbackRequest,
    db: AsyncSession = Depends(get_db),
) -> ResourceFeedbackResponse:
    """Record whether a resource was helpful. One vote per resource per session."""
    if not await session_exists(db, feedback.session_id):
        raise HTTPException(status_code=404, detail="Session not found")

    await insert_resource_feedback(db, feedback)

    return ResourceFeedbackResponse(
        success=True,
        resource_id=feedback.resource_id,
        helpful=feedback.helpful,
    )


@router.get("/validate/{token}")
async def validate_feedback_token(
    token: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Validate a feedback token. Returns 200 if valid, 410 if expired, 404 if unknown."""
    session_id = await _require_valid_token(db, token)
    return {"valid": True, "session_id": session_id}


@router.post("/visit", response_model=VisitFeedbackResponse)
async def submit_visit_feedback(
    feedback: VisitFeedbackRequest,
    db: AsyncSession = Depends(get_db),
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

    return VisitFeedbackResponse(success=True)

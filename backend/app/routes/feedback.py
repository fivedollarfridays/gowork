"""Feedback routes — resource and visit feedback endpoints."""

import json
import time

from fastapi import APIRouter, Depends, HTTPException, Request
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


class _FeedbackRateLimiter:
    """Simple in-memory rate limiter for feedback endpoints."""

    def __init__(self, max_requests: int = 20, window_seconds: int = 60):
        self._max = max_requests
        self._window = window_seconds
        self._requests: dict[str, list[float]] = {}

    def check(self, key: str) -> bool:
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
        self._requests.clear()


_rate_limiter = _FeedbackRateLimiter()


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
    http_request: Request,
    db: AsyncSession = Depends(get_db),
) -> ResourceFeedbackResponse:
    """Record whether a resource was helpful. One vote per resource per session."""
    client_ip = http_request.client.host if http_request.client else "unknown"
    if not _rate_limiter.check(client_ip):
        raise HTTPException(status_code=429, detail="Too many requests. Please try again later.")
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
    http_request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Validate a feedback token. Returns 200 if valid, 410 if expired, 404 if unknown."""
    client_ip = http_request.client.host if http_request.client else "unknown"
    if not _rate_limiter.check(client_ip):
        raise HTTPException(status_code=429, detail="Too many requests. Please try again later.")
    session_id = await _require_valid_token(db, token)
    return {"valid": True, "session_id": session_id}


@router.post("/visit", response_model=VisitFeedbackResponse)
async def submit_visit_feedback(
    feedback: VisitFeedbackRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_db),
) -> VisitFeedbackResponse:
    """Record visit feedback. One submission per session."""
    client_ip = http_request.client.host if http_request.client else "unknown"
    if not _rate_limiter.check(client_ip):
        raise HTTPException(status_code=429, detail="Too many requests. Please try again later.")
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

"""Admin draft-generation endpoint for the assessment authoring layer (T23.3).

Exposes ``POST /api/admin/assessments/draft`` — gated on
``admin`` OR ``sme_reviewer``, rate-limited to 10/hour per account,
calls :func:`app.ai.assessment_drafter.draft_questions`, persists via
:func:`app.core.queries_assessments.create_assessment` +
:func:`app.core.queries_assessments.create_draft_version`, and returns
the ``{assessment_id, version_id, status, question_count}`` envelope.

This route deliberately lives in its own module rather than extending
:mod:`app.routes.auth` (already at the per-file warning threshold) and
its own router so T23.4's reviewer-queue API can be added without
touching this file.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.assessment_drafter import draft_questions
from app.core import queries_assessments
from app.core.assessments_schema import ASSESSMENT_KINDS, ASSESSMENT_TRACKS
from app.core.auth_roles import any_of_roles
from app.core.database import get_db
from app.core.rate_limit import RateLimiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/assessments", tags=["admin"])

_HOUR_SECONDS = 60 * 60

# Per-account drafter quota — protects ANTHROPIC_API_KEY spend and gives
# the reviewer queue a sane upper bound on draft churn. In-memory: same
# anonymous-first invariant that the magic-link limiter follows; an
# acceptable trade-off for a per-account, per-hour bucket.
_account_limiter = RateLimiter(
    max_requests=10, window_seconds=_HOUR_SECONDS,
)


class DraftRequest(BaseModel):
    """Request body for ``POST /api/admin/assessments/draft``."""

    slug: str = Field(..., min_length=1, max_length=120)
    kind: str
    track: str
    source_prompt: str = Field(..., min_length=1, max_length=4000)


def _validate_enums(kind: str, track: str) -> None:
    """Guard the kind/track tuples before paying for an LLM call."""
    if kind not in ASSESSMENT_KINDS:
        raise HTTPException(
            status_code=422,
            detail=f"kind must be one of {ASSESSMENT_KINDS}",
        )
    if track not in ASSESSMENT_TRACKS:
        raise HTTPException(
            status_code=422,
            detail=f"track must be one of {ASSESSMENT_TRACKS}",
        )


def _enforce_account_limit(account_id: int) -> None:
    """Raise 429 when the per-account hourly budget is exhausted."""
    if not _account_limiter.check(str(account_id)):
        logger.info(
            "assessment_drafter rate-limited account_id=%s", account_id,
        )
        raise HTTPException(
            status_code=429,
            detail=(
                "Too many draft requests. "
                "Maximum 10 per hour per account."
            ),
        )


async def _generate_drafts(body: DraftRequest) -> list[dict]:
    """Call the drafter; map malformed Claude output to a sanitized 502."""
    try:
        drafts = await draft_questions(
            kind=body.kind,
            track=body.track,
            source_prompt=body.source_prompt,
        )
    except ValueError:
        # Sanitized: do not echo the raw Claude bytes back to clients.
        logger.warning(
            "assessment_drafter malformed LLM response slug=%s",
            body.slug, exc_info=True,
        )
        raise HTTPException(
            status_code=502,
            detail="Upstream model returned a malformed response.",
        ) from None
    return [d.to_question_row(i + 1) for i, d in enumerate(drafts)]


async def _persist_draft(
    db: AsyncSession,
    *,
    body: DraftRequest,
    account_id: int,
    questions: list[dict],
) -> tuple[int, int]:
    """Create the assessment + draft version atomically (per helper)."""
    assessment_id = await queries_assessments.create_assessment(
        db,
        slug=body.slug,
        kind=body.kind,
        track=body.track,
        created_by=account_id,
    )
    version_id = await queries_assessments.create_draft_version(
        db,
        assessment_id=assessment_id,
        drafted_by=account_id,
        questions=questions,
    )
    return assessment_id, version_id


@router.post("/draft")
async def create_draft(
    body: DraftRequest,
    db: AsyncSession = Depends(get_db),
    account: dict = Depends(any_of_roles("admin", "sme_reviewer")),
) -> dict:
    """Draft + persist a new assessment version from *body.source_prompt*.

    Returns 200 with ``{assessment_id, version_id, status: "draft",
    question_count}``. Errors:

    * 403 — caller is anonymous or holds neither ``admin`` nor
      ``sme_reviewer`` (handled by ``any_of_roles``).
    * 422 — kind/track outside the canonical enums.
    * 429 — per-account hourly limit (10/hour) exhausted.
    * 502 — Claude returned a malformed response.
    """
    _validate_enums(body.kind, body.track)
    account_id = int(account["id"])
    _enforce_account_limit(account_id)
    questions = await _generate_drafts(body)
    assessment_id, version_id = await _persist_draft(
        db, body=body, account_id=account_id, questions=questions,
    )
    logger.info(
        "assessment_drafter created assessment_id=%s version_id=%s "
        "questions=%d", assessment_id, version_id, len(questions),
    )
    return {
        "assessment_id": assessment_id,
        "version_id": version_id,
        "status": "draft",
        "question_count": len(questions),
    }

"""'What Happens If' multi-barrier simulator endpoint.

Accepts barrier toggles and returns cascading impact analysis:
- Which barriers remain vs resolved
- What new barriers become unlockable
- Estimated job accessibility improvement
- Benefits that become available
"""

import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import require_session_token
from app.core.database import get_db
from app.core.queries import get_session_by_id
from app.modules.plan.barrier_sequencer import sequence_barriers

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["simulate"])


class SimulateRequest(BaseModel):
    """Request body for the barrier simulator."""

    session_id: str = Field(pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
    resolved_barriers: list[str] = Field(default_factory=list, max_length=10)


class SimulateResponse(BaseModel):
    """Response from the barrier simulator."""

    barriers_resolved: list[str]
    barriers_remaining: list[str]
    unlocked_barriers: list[str]
    jobs_unlocked_estimate: int
    benefits_unlocked: list[str]
    sequence_after: dict


# Rough estimates for job accessibility improvement per barrier resolution
_JOBS_PER_BARRIER = {
    "criminal_record": 15,
    "credit": 8,
    "transportation": 12,
    "childcare": 10,
    "housing": 5,
    "health": 4,
    "training": 6,
}

# Benefits that become accessible when barriers are resolved
_BENEFITS_PER_BARRIER = {
    "criminal_record": ["Fair-chance employer pool", "Bonding programs"],
    "credit": ["Financial literacy programs", "Credit counseling"],
    "childcare": ["Childcare subsidy", "Head Start"],
    "transportation": ["Transit pass programs"],
    "housing": ["Section 8 eligibility", "Rapid rehousing"],
    "health": ["Medicaid", "Community health centers"],
    "training": ["WIOA training vouchers", "Pell grants"],
}


def _compute_unlocked(
    all_barriers: list[str], resolved: set[str],
) -> list[str]:
    """Determine which barriers become 'unlockable' after resolution."""
    if not all_barriers or not resolved:
        return []
    remaining = [b for b in all_barriers if b not in resolved]
    sequence = sequence_barriers(all_barriers)
    unlocked = []
    for step in sequence.steps:
        if step.barrier_id in resolved:
            for u in step.unlocks:
                if u in remaining and u not in unlocked:
                    unlocked.append(u)
    return unlocked


@router.post("/simulate", response_model=SimulateResponse)
async def simulate_barrier_resolution(
    body: SimulateRequest,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
) -> SimulateResponse:
    """Simulate the effect of resolving one or more barriers."""
    await require_session_token(db, body.session_id, token)

    row = await get_session_by_id(db, body.session_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Session not found")

    barriers_raw = row.get("barriers", "[]")
    all_barriers = json.loads(barriers_raw) if isinstance(barriers_raw, str) else barriers_raw

    resolved_set = set(body.resolved_barriers)
    remaining = [b for b in all_barriers if b not in resolved_set]

    # Compute cascading unlocks
    unlocked = _compute_unlocked(all_barriers, resolved_set)

    # Estimate additional jobs
    jobs_estimate = sum(_JOBS_PER_BARRIER.get(b, 3) for b in body.resolved_barriers)

    # Collect benefits unlocked
    benefits = []
    for b in body.resolved_barriers:
        benefits.extend(_BENEFITS_PER_BARRIER.get(b, []))

    # Compute new sequence for remaining barriers
    sequence_after = sequence_barriers(remaining)

    return SimulateResponse(
        barriers_resolved=body.resolved_barriers,
        barriers_remaining=remaining,
        unlocked_barriers=unlocked,
        jobs_unlocked_estimate=jobs_estimate,
        benefits_unlocked=benefits,
        sequence_after=sequence_after.model_dump(),
    )

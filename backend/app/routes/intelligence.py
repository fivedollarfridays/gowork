"""Community barrier intelligence endpoint.

Returns calibrated barrier resolution statistics derived from
visit feedback, closing the N+1 feedback loop. No PII is exposed --
only aggregate statistics.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.outcomes.intelligence import compute_calibrated_barriers
from app.modules.outcomes.intelligence_queries import get_barrier_feedback_rows
from app.modules.plan.barrier_sequencer import _WEEKS_PER_BARRIER

router = APIRouter(prefix="/api/intelligence", tags=["intelligence"])


@router.get("/barriers")
async def get_barrier_intelligence(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return calibrated barrier resolution stats from community outcomes.

    Response includes:
    - barriers: per-barrier calibrated stats (avg_weeks, success_rate, etc.)
    - confidence: overall confidence level
    - calibrated_weeks: dict of barrier_id -> calibrated weeks (MEDIUM+ only)
    - default_weeks: hardcoded defaults for comparison
    """
    rows = await get_barrier_feedback_rows(db)
    result = compute_calibrated_barriers(rows)

    return {
        "barriers": [b.model_dump() for b in result.barriers],
        "confidence": result.confidence.value,
        "calibrated_weeks": result.to_weeks_dict(),
        "default_weeks": dict(_WEEKS_PER_BARRIER),
    }

"""Community barrier intelligence endpoint.

Returns calibrated barrier resolution statistics derived from
visit feedback, closing the N+1 feedback loop. No PII is exposed --
only aggregate statistics.

T12.12 / T12.33 ADDITIVE: the response now carries an
`application_conversion_rates` key sourced from
`jobs.funnel_analytics.build_application_conversion_rates`. All
pre-existing fields are untouched; k-anonymity (min=5) is enforced
inside the analytics module.
"""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.modules.jobs.funnel_analytics import build_application_conversion_rates
from app.modules.outcomes.intelligence import compute_calibrated_barriers
from app.modules.outcomes.intelligence_queries import get_barrier_feedback_rows
from app.modules.plan.barrier_sequencer import _WEEKS_PER_BARRIER

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/intelligence", tags=["intelligence"])


def _serialize_application_conversion_rates() -> dict:
    """Safely build application_conversion_rates; never break the endpoint."""
    try:
        settings = get_settings()
        db_path = settings.database_url.replace("sqlite+aiosqlite:///", "")
        raw = build_application_conversion_rates(settings.city, db_path=db_path)
        return {slice_key: {k: v.model_dump() for k, v in slice_val.items()}
                for slice_key, slice_val in raw.items()}
    except Exception:  # defensive: must not break existing response
        logger.warning(
            "build_application_conversion_rates failed; returning empty",
            exc_info=True,
        )
        return {"city_scoped": {}, "by_cleared_barriers": {}, "by_fair_chance": {}}


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
    - application_conversion_rates: T12.12 additive — city-scoped jobs funnel
    """
    rows = await get_barrier_feedback_rows(db)
    result = compute_calibrated_barriers(rows)

    return {
        "barriers": [b.model_dump() for b in result.barriers],
        "confidence": result.confidence.value,
        "calibrated_weeks": result.to_weeks_dict(),
        "default_weeks": dict(_WEEKS_PER_BARRIER),
        "total_feedback_count": result.total_feedback_count,
        "avg_plan_accuracy": result.avg_plan_accuracy,
        "application_conversion_rates": _serialize_application_conversion_rates(),
    }

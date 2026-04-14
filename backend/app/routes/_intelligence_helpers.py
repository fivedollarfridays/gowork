"""Shared helpers for intelligence-enriched route responses.

Used by both the pathway route and plan_intelligence route to build
community intelligence metadata and parse benefits profiles.
"""

import json
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.benefits.types import BenefitsProfile
from app.modules.outcomes.intelligence import CalibratedWeeks, compute_calibrated_barriers
from app.modules.outcomes.intelligence_queries import get_barrier_feedback_rows
from app.modules.plan.barrier_sequencer import _WEEKS_PER_BARRIER

logger = logging.getLogger(__name__)


def build_community_intelligence(
    calibrated_weeks: dict[str, int],
    total_feedback: int,
    barriers: list[dict],
) -> dict:
    """Build the community_intelligence block for API responses.

    Shows calibrated barrier stats and improvements from defaults,
    making the N+1 loop visible to the frontend.
    """
    calibrated_barriers = {
        b["barrier_id"]: {
            "avg_weeks": b["avg_weeks"],
            "confidence": b["confidence"],
            "sample_size": b["sample_size"],
        }
        for b in barriers
    }
    defaults = dict(_WEEKS_PER_BARRIER)
    improvements: dict[str, dict] = {}
    for bid, cal_weeks in calibrated_weeks.items():
        default_val = defaults.get(bid)
        if default_val is not None:
            improvements[bid] = {
                "default": default_val,
                "calibrated": cal_weeks,
                "improved": cal_weeks != default_val,
            }
    return {
        "total_feedback": total_feedback,
        "calibrated_barriers": calibrated_barriers,
        "improvements_from_defaults": improvements,
    }


def parse_benefits_profile(row: dict) -> BenefitsProfile:
    """Parse benefits profile from session row, falling back to defaults."""
    bp_raw = row.get("benefits_profile")
    if bp_raw:
        try:
            bp_data = json.loads(bp_raw) if isinstance(bp_raw, str) else bp_raw
            return BenefitsProfile(**bp_data)
        except (json.JSONDecodeError, ValueError):
            return BenefitsProfile()
    return BenefitsProfile()


async def fetch_intelligence(db: AsyncSession) -> CalibratedWeeks:
    """Fetch calibrated barrier data from the intelligence engine.

    Handles DB errors gracefully by returning empty calibration.
    """
    try:
        rows = await get_barrier_feedback_rows(db)
        return compute_calibrated_barriers(rows)
    except Exception:
        logger.warning("Intelligence fetch failed, using defaults", exc_info=True)
        return compute_calibrated_barriers([])

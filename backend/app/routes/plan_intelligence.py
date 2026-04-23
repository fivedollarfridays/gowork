"""Unified Plan Intelligence endpoint -- one call to rule them all.

Returns EVERYTHING a frontend needs for the complete barrier resolution
+ career trajectory view: barriers (sequenced), pathway (calibrated
with community data), cliff analysis, and community stats.

Closes the N+1 feedback loop by fetching calibrated_weeks from the
intelligence engine at request time.
"""

from __future__ import annotations

import json
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.cities.config import get_city_config
from app.core.auth import require_session_token
from app.core.config import get_settings
from app.core.database import get_db
from app.core.queries import get_session_by_id
from app.modules.benefits.cliff_calculator import calculate_cliff_analysis
from app.modules.outcomes.community_insights import generate_insights
from app.modules.pathway.engine import generate_pathways
from app.modules.plan.barrier_sequencer import sequence_barriers
from app.routes._appointments_helpers import resolve_db_path
from app.routes._intelligence_helpers import (
    build_community_intelligence,
    fetch_intelligence,
    parse_benefits_profile,
    run_pathway_linker_hook,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/plan", tags=["plan_intelligence"])

_UUID_RE = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
SessionId = Annotated[str, Path(pattern=_UUID_RE)]


@router.get("/{session_id}/intelligence")
async def get_plan_intelligence(
    session_id: SessionId,
    token: str = Query(...),
    current_wage: float = Query(default=0.0, ge=0.0, le=100.0),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return complete plan intelligence in a single call.

    Combines barrier sequence, career pathway, cliff analysis,
    community intelligence, and personalized insights.
    """
    await require_session_token(db, session_id, token)

    row = await get_session_by_id(db, session_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Session not found")

    barriers_raw = row.get("barriers", "[]")
    barriers = json.loads(barriers_raw) if isinstance(barriers_raw, str) else barriers_raw
    profile = parse_benefits_profile(row)

    intelligence = await fetch_intelligence(db)
    return _build_intelligence_response(
        session_id, intelligence, barriers, profile, current_wage,
    )


def _build_intelligence_response(
    session_id: str,
    intelligence: CalibratedWeeks,
    barriers: list[str],
    profile: dict,
    current_wage: float,
) -> dict:
    """Assemble all intelligence sections into the unified response."""
    calibrated_weeks = intelligence.to_weeks_dict()

    sequence = sequence_barriers(barriers, calibrated_weeks=calibrated_weeks or None)
    pathway_result = generate_pathways(
        barrier_ids=barriers,
        benefits_profile=profile,
        current_wage=current_wage,
        calibrated_weeks=calibrated_weeks or None,
    )
    run_pathway_linker_hook(
        session_id, pathway_result, city=get_settings().city, db_path=resolve_db_path(),
    )
    cliff = calculate_cliff_analysis(profile)
    community = build_community_intelligence(
        calibrated_weeks,
        intelligence.total_feedback_count,
        [b.model_dump() for b in intelligence.barriers],
    )

    city_config = get_city_config()
    insights = generate_insights(intelligence, barriers, city_config.name)

    return {
        "barriers": sequence.model_dump(),
        "pathway": pathway_result.model_dump(),
        "cliff_analysis": cliff.model_dump(),
        "community_intelligence": community,
        "insights": [i.model_dump() for i in insights],
    }

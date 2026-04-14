"""Standalone Community Insights endpoint.

GET /api/insights/{session_id} returns personalized 'People Like You'
community insight messages based on the session's barrier profile
and calibrated outcome data from the intelligence engine.

No LLM calls. Fully deterministic. City-aware.
"""

import json
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.cities.config import get_city_config
from app.core.auth import require_session_token
from app.core.database import get_db
from app.core.queries import get_session_by_id
from app.modules.outcomes.community_insights import generate_insights
from app.routes._intelligence_helpers import fetch_intelligence

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/insights", tags=["insights"])

_UUID_RE = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
SessionId = Annotated[str, Path(pattern=_UUID_RE)]


@router.get("/{session_id}")
async def get_community_insights(
    session_id: SessionId,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return personalized community insights for a session.

    Fetches the session's barriers, runs them through the intelligence
    engine, and generates human-readable insight messages.
    """
    await require_session_token(db, session_id, token)

    row = await get_session_by_id(db, session_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Session not found")

    barriers_raw = row.get("barriers", "[]")
    barriers = json.loads(barriers_raw) if isinstance(barriers_raw, str) else barriers_raw

    city_config = get_city_config()
    city_name = city_config.name

    intelligence = await fetch_intelligence(db)
    insights = generate_insights(intelligence, barriers, city_name)

    return {
        "insights": [i.model_dump() for i in insights],
        "barrier_count": len(barriers),
        "city": city_name,
    }

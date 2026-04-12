"""Career pathway endpoint -- multi-step trajectory generation.

Accepts a session ID and current wage, returns ranked career pathways
that fuse barrier sequencing, cliff navigation, and wage progression
into actionable multi-step career plans.
"""

import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import require_session_token
from app.core.database import get_db
from app.core.queries import get_session_by_id
from app.modules.benefits.types import BenefitsProfile
from app.modules.pathway.engine import generate_pathways

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["pathway"])

_UUID_PATTERN = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"


class PathwayRequest(BaseModel):
    """Request body for pathway generation."""

    session_id: str = Field(pattern=_UUID_PATTERN)
    current_wage: float = Field(default=0.0, ge=0.0, le=100.0)


@router.post("/pathway")
async def generate_career_pathways(
    body: PathwayRequest,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Generate ranked career pathways for a session."""
    await require_session_token(db, body.session_id, token)

    row = await get_session_by_id(db, body.session_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Session not found")

    # Parse barriers
    barriers_raw = row.get("barriers", "[]")
    barriers = json.loads(barriers_raw) if isinstance(barriers_raw, str) else barriers_raw

    # Parse benefits profile if available
    bp_raw = row.get("benefits_profile")
    if bp_raw:
        try:
            bp_data = json.loads(bp_raw) if isinstance(bp_raw, str) else bp_raw
            profile = BenefitsProfile(**bp_data)
        except (json.JSONDecodeError, ValueError):
            profile = BenefitsProfile()
    else:
        profile = BenefitsProfile()

    result = generate_pathways(
        barrier_ids=barriers,
        benefits_profile=profile,
        current_wage=body.current_wage,
    )

    return result.model_dump()

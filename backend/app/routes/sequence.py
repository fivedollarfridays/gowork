"""Barrier sequence endpoint — topologically sorted resolution order."""

import json
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import require_session_token
from app.core.database import get_db
from app.core.queries import get_session_by_id
from app.modules.plan.barrier_sequencer import sequence_barriers

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/plan", tags=["sequence"])

_UUID_RE = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
SessionId = Annotated[str, Path(pattern=_UUID_RE)]


def _map_barrier_to_graph_id(barrier_type: str) -> str | None:
    """Map assessment barrier types to barrier graph IDs."""
    mapping = {
        "credit": "credit",
        "transportation": "transportation",
        "childcare": "childcare",
        "housing": "housing",
        "health": "health",
        "training": "training",
        "criminal_record": "criminal_record",
    }
    return mapping.get(barrier_type)


@router.get("/{session_id}/sequence")
async def get_barrier_sequence(
    session_id: SessionId,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return the topologically sorted barrier resolution sequence."""
    await require_session_token(db, session_id, token)

    row = await get_session_by_id(db, session_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Session not found")

    barriers_raw = row.get("barriers", "[]")
    barriers = json.loads(barriers_raw) if isinstance(barriers_raw, str) else barriers_raw

    # Map barrier types to graph node IDs
    graph_ids = []
    for b in barriers:
        gid = _map_barrier_to_graph_id(b)
        if gid:
            graph_ids.append(gid)

    sequence = sequence_barriers(graph_ids)
    return sequence.model_dump()

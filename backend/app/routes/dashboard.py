"""Case manager dashboard and aggregate outcomes endpoints."""

import json
import logging
from collections import Counter

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["dashboard"])


async def _get_all_session_barriers(db: AsyncSession) -> tuple[int, list[str]]:
    """Fetch all sessions and extract barrier lists. Returns (count, flat barrier list)."""
    result = await db.execute(text("SELECT barriers FROM sessions"))
    rows = result.fetchall()
    all_barriers: list[str] = []
    for row in rows:
        raw = row[0]
        if raw:
            try:
                barriers = json.loads(raw) if isinstance(raw, str) else raw
                if isinstance(barriers, list):
                    all_barriers.extend(barriers)
            except (json.JSONDecodeError, TypeError):
                continue
    return len(rows), all_barriers


@router.get("/dashboard/stats")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return aggregate dashboard metrics for case managers."""
    total, all_barriers = await _get_all_session_barriers(db)
    counter = Counter(all_barriers)
    common = [{"barrier": b, "count": c} for b, c in counter.most_common(10)]

    return {
        "total_assessments": total,
        "common_barriers": common,
        "total_barrier_instances": len(all_barriers),
    }


@router.get("/outcomes/aggregate")
async def get_aggregate_outcomes(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return anonymized aggregate outcome data for the landing page."""
    total, all_barriers = await _get_all_session_barriers(db)
    counter = Counter(all_barriers)
    top = [{"barrier": b, "count": c} for b, c in counter.most_common(5)]

    return {
        "assessment_count": total,
        "top_barriers": top,
    }

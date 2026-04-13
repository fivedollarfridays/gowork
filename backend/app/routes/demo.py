"""Demo seed admin endpoint.

Provides POST /api/demo/seed to populate realistic Fort Worth data
for the HackFW 2026 demo. Protected by admin key.
"""

import logging

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.demo_seed import run_demo_seed

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/demo", tags=["demo"])

_ADMIN_KEY = "montgowork-demo-2026"


def _require_admin_key(
    x_admin_key: str | None = Header(default=None),
) -> None:
    """Verify the admin key header is present and correct."""
    if not x_admin_key or x_admin_key != _ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Invalid admin key")


@router.post("/seed")
async def seed_demo_data(
    db: AsyncSession = Depends(get_db),
    _: None = Depends(_require_admin_key),
) -> dict:
    """Seed realistic Fort Worth demo data into the database.

    Requires X-Admin-Key header. Idempotent: returns already_seeded
    if demo data has been created before.
    """
    result = await db.execute(text("SELECT COUNT(*) FROM sessions"))
    count = result.scalar()
    if count >= 50:
        return {"already_seeded": True, "sessions_existing": count}

    summary = await run_demo_seed(db)
    logger.info("Demo seed complete: %s", summary)
    return summary

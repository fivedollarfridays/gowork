"""Seed Honest Jobs fair-chance listings into job_listings table."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.queries_jobs import insert_job_listings

logger = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"
_SEED_FILE = "honestjobs_listings.json"


async def seed_honestjobs_listings(session: AsyncSession) -> int:
    """Idempotent seed of Honest Jobs listings. Returns count inserted."""
    filepath = _DATA_DIR / _SEED_FILE
    if not filepath.exists():
        logger.warning("Honest Jobs seed file missing: %s", filepath)
        return 0

    data = json.loads(filepath.read_text())
    if not data:
        return 0

    # Check existing to avoid duplicates (by source + title + company)
    result = await session.execute(
        text("SELECT title, company FROM job_listings WHERE source = 'honestjobs'")
    )
    existing = {(row[0], row[1]) for row in result}

    now = datetime.now(timezone.utc).isoformat()
    listings = []
    for record in data:
        key = (record.get("title"), record.get("company"))
        if key in existing:
            continue
        listings.append({
            "title": record["title"],
            "company": record.get("company"),
            "location": record.get("location"),
            "description": record.get("description"),
            "url": record.get("url"),
            "source": "honestjobs",
            "scraped_at": record.get("scraped_at", now),
            "fair_chance": 1,
        })

    if not listings:
        return 0

    return await insert_job_listings(session, listings)

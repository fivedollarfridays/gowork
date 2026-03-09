"""Employer policy seed data loader — idempotent INSERT OR IGNORE."""

import json
import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import resolve_data_dir

logger = logging.getLogger(__name__)

_SEED_FILE = "employer_policies_seed.json"


async def seed_employer_policies(session: AsyncSession) -> None:
    """Idempotently insert employer policies from seed JSON. Safe to re-run."""
    filepath = resolve_data_dir() / _SEED_FILE
    if not filepath.exists():
        logger.warning("employer_policies_seed.json not found at %s", filepath)
        return

    data = json.loads(filepath.read_text())
    count = 0
    for record in data:
        await session.execute(
            text(
                "INSERT OR IGNORE INTO employer_policies "
                "(employer_name, fair_chance, excluded_charges, "
                "lookback_years, bg_check_timing, industry, source, "
                "montgomery_area) "
                "VALUES (:name, :fc, :exc, :lb, :bgt, :ind, :src, :ma)"
            ),
            {
                "name": record["employer_name"],
                "fc": 1 if record.get("fair_chance") else 0,
                "exc": json.dumps(record.get("excluded_charges", [])),
                "lb": record.get("lookback_years"),
                "bgt": record.get("bg_check_timing", "pre_offer"),
                "ind": record.get("industry"),
                "src": record.get("source"),
                "ma": 1 if record.get("montgomery_area", True) else 0,
            },
        )
        count += 1
    await session.commit()
    logger.info("Employer policies seeded: %d records processed", count)

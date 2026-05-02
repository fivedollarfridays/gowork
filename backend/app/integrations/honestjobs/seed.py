"""Seed Honest Jobs fair-chance listings into job_listings table."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.queries_jobs import insert_job_listings

logger = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"
_SEED_FILE = "honestjobs_listings.json"


def _resolve_seed_path() -> Path:
    """Resolve the seed JSON path for the active CITY.

    Layer 1 of the city-aware jobs pipeline. Looks first under
    ``data/cities/<city>/honestjobs_listings.json``, then falls back to
    the legacy ``data/honestjobs_listings.json`` so unknown CITY values
    fail safe to "no jobs" rather than crashing.
    """
    settings = get_settings()
    city_path = _DATA_DIR / "cities" / settings.city / _SEED_FILE
    if city_path.exists():
        return city_path
    return _DATA_DIR / _SEED_FILE


def _all_seed_paths() -> list[Path]:
    """Return the seed file path for every configured city (existing only).

    Walks ``data/cities/*/honestjobs_listings.json`` so a single startup
    seeds Fort Worth + Montgomery + any future city.  ``_filter_by_state``
    in :mod:`app.modules.matching.job_matcher` keeps each request's
    listings scoped to the user's state at query time.

    Falls back to the active-CITY single-file path when no per-city
    directory exists yet (legacy single-tenant deployments).
    """
    cities_root = _DATA_DIR / "cities"
    paths: list[Path] = []
    if cities_root.is_dir():
        for child in sorted(cities_root.iterdir()):
            candidate = child / _SEED_FILE
            if candidate.exists():
                paths.append(candidate)
    if paths:
        return paths
    fallback = _resolve_seed_path()
    return [fallback] if fallback.exists() else []


def _row_from_record(record: dict, now: str) -> dict:
    """Map a JSON record to the insert_job_listings row shape.

    ``lat`` / ``lng`` (m010) and ``credit_check`` / ``fair_chance``
    pass through when present; missing -> sensible defaults that
    keep legacy seed files (no coords, no credit flag) compatible.
    """
    return {
        "title": record["title"],
        "company": record.get("company"),
        "location": record.get("location"),
        "description": record.get("description"),
        "url": record.get("url"),
        "source": "honestjobs",
        "scraped_at": record.get("scraped_at", now),
        "fair_chance": record.get("fair_chance", 1),
        "credit_check": record.get("credit_check", "unknown"),
        "lat": record.get("lat"),
        "lng": record.get("lng"),
    }


async def seed_honestjobs_listings(session: AsyncSession) -> int:
    """Idempotent seed of Honest Jobs listings, EVERY city.

    Iterates ``data/cities/*/honestjobs_listings.json`` so the resulting
    DB carries every city's fair-chance listings.  ``_filter_by_state``
    keeps each user's response scoped to the right state at query time.
    """
    seed_paths = _all_seed_paths()
    if not seed_paths:
        logger.warning("Honest Jobs seed files missing under %s", _DATA_DIR)
        return 0
    result = await session.execute(
        text("SELECT title, company FROM job_listings WHERE source = 'honestjobs'")
    )
    existing: set[tuple[str | None, str | None]] = {
        (row[0], row[1]) for row in result
    }
    now = datetime.now(timezone.utc).isoformat()
    listings: list[dict] = []
    for filepath in seed_paths:
        data = json.loads(filepath.read_text())
        if not data:
            continue
        for record in data:
            key = (record.get("title"), record.get("company"))
            if key in existing:
                continue
            existing.add(key)
            listings.append(_row_from_record(record, now))
    if not listings:
        return 0
    return await insert_job_listings(session, listings)

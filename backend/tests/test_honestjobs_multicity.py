"""Tests for honestjobs multi-city seeding.

A single backend startup must seed every configured city's Honest Jobs
listings into the same ``job_listings`` table.  Without this, a
Montgomery request lands on a DB where only Fort Worth listings were
seeded (the active CITY at startup) and ``match_jobs`` returns zero
matches after the state filter.

Defense-in-depth at the matcher (``_filter_by_state``) keeps the
correct city's listings flowing — but only if those listings were
seeded in the first place.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


def _fresh_async_db_url() -> tuple[str, str]:
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    return f"sqlite+aiosqlite:///{path}", path


@pytest.mark.asyncio
async def test_seed_loads_listings_from_every_city():
    """After startup, both AL and TX listings live in job_listings."""
    db_url, db_path = _fresh_async_db_url()
    try:
        from app.core.database import init_db
        from app.integrations.honestjobs.seed import seed_honestjobs_listings

        engine = create_async_engine(db_url, echo=False)
        await init_db(engine)
        sm = async_sessionmaker(engine, expire_on_commit=False)
        async with sm() as session:
            await seed_honestjobs_listings(session)
            await session.commit()
        async with engine.begin() as conn:
            res = await conn.execute(text(
                "SELECT location FROM job_listings WHERE source = 'honestjobs'"
            ))
            locations = [row[0] for row in res.fetchall()]
        await engine.dispose()
        # Both cities present.  ``_filter_by_state`` does state-suffix
        # matching, so just ensure each state suffix appears at least
        # once.
        assert any((loc or "").lower().endswith(", tx") for loc in locations), \
            f"no Texas listings; locs={locations}"
        assert any((loc or "").lower().endswith(", al") for loc in locations), \
            f"no Alabama listings; locs={locations}"
    finally:
        os.unlink(db_path)

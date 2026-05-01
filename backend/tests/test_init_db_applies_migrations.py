"""Tests that ``init_db`` applies migrations beyond the m001 baseline.

Without this, runtime DBs never grow the new ``resources.city`` column
because ``init_db`` only executes ``DDL_SQL`` (which is the m001
baseline) and skips m002+ migrations entirely.

The fix wires ``app.core.migrations.runner.apply_pending`` into the
post-DDL path so every migration that targets m001 tables is applied
on first boot.
"""

from __future__ import annotations

import asyncio
import os
import tempfile

import pytest


def _fresh_db_url() -> tuple[str, str]:
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    return f"sqlite+aiosqlite:///{path}", path


@pytest.mark.asyncio
async def test_init_db_creates_city_column_on_resources():
    """init_db should run all migrations; resources.city must exist."""
    db_url, db_path = _fresh_db_url()
    try:
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import create_async_engine

        engine = create_async_engine(db_url, echo=False)
        from app.core.database import init_db

        await init_db(engine)
        async with engine.begin() as conn:
            res = await conn.execute(text("PRAGMA table_info(resources)"))
            cols = {row[1] for row in res.fetchall()}
        await engine.dispose()
        assert "city" in cols, f"resources.city missing; saw cols={cols}"
    finally:
        os.unlink(db_path)

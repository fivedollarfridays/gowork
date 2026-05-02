"""Tests for city-tagged resources: schema, seeding, and per-city query.

These tests cover the chokepoint that prevents Alabama resources from
leaking into Fort Worth assessments (and vice versa). The DB grows a
``city`` column on the ``resources`` table; the seeder tags each row
with its source city slug; the query filters by per-request context.
"""

from __future__ import annotations

import asyncio
import json
import os
import sqlite3
import tempfile
import unittest

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


# ── Cycle 1: schema migration ──────────────────────────────────────


class TestResourcesCityColumnMigration:
    """A new migration adds ``city`` column to ``resources``."""

    def _fresh_db(self) -> str:
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        return path

    def test_city_column_exists_after_migrations(self):
        from app.core.migrations import runner

        path = self._fresh_db()
        try:
            runner.apply_pending(path)
            conn = sqlite3.connect(path)
            try:
                cols = {row[1] for row in conn.execute("PRAGMA table_info(resources)")}
            finally:
                conn.close()
            assert "city" in cols, "resources.city column missing after migrations"
        finally:
            os.unlink(path)

    def test_city_column_is_indexed_for_query_perf(self):
        from app.core.migrations import runner

        path = self._fresh_db()
        try:
            runner.apply_pending(path)
            conn = sqlite3.connect(path)
            try:
                idx_rows = list(
                    conn.execute("PRAGMA index_list(resources)")
                )
                idx_names = {row[1] for row in idx_rows}
            finally:
                conn.close()
            assert any("city" in name.lower() for name in idx_names), \
                f"no index on resources.city found; saw: {idx_names}"
        finally:
            os.unlink(path)

    def test_city_column_default_does_not_break_legacy_inserts(self):
        """Existing INSERTs that don't supply city still succeed."""
        from app.core.migrations import runner

        path = self._fresh_db()
        try:
            runner.apply_pending(path)
            conn = sqlite3.connect(path)
            try:
                conn.execute(
                    "INSERT INTO resources (name, category) VALUES (?, ?)",
                    ("Test Resource", "social_service"),
                )
                conn.commit()
                row = conn.execute(
                    "SELECT name, city FROM resources WHERE name = 'Test Resource'"
                ).fetchone()
                # City may be NULL or "" for legacy rows — both acceptable.
                assert row[0] == "Test Resource"
            finally:
                conn.close()
        finally:
            os.unlink(path)


# ── Cycle 2: seeder loads every city's resources tagged by slug ───


def _fresh_async_db_url() -> tuple[str, str]:
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    return f"sqlite+aiosqlite:///{path}", path


@pytest.mark.asyncio
async def test_seeder_loads_fort_worth_resources_tagged_with_city():
    """Fort-worth seed file rows arrive tagged ``city='fort-worth'``."""
    db_url, db_path = _fresh_async_db_url()
    try:
        engine = create_async_engine(db_url, echo=False)
        from app.core.database import init_db

        await init_db(engine)
        async with engine.begin() as conn:
            res = await conn.execute(text(
                "SELECT name, city FROM resources WHERE city = 'fort-worth'"
            ))
            rows = res.fetchall()
        await engine.dispose()
        names = {row[0] for row in rows}
        assert "Workforce Solutions for Tarrant County" in names
        # Stage-2 expanded the Trinity Metro entries into specific sub-
        # services (Bus / TEXRail / TRE / ZIPZONE / Bike Share / paratransit).
        # Any of these proves the seeder picked up the active city's file.
        assert any(
            "Trinity Metro" in n or "TEXRail" in n or "TRE" in n
            for n in names
        ), names
        # Every row must carry the city tag.
        for _name, city in rows:
            assert city == "fort-worth"
    finally:
        os.unlink(db_path)


@pytest.mark.asyncio
async def test_seeder_loads_montgomery_resources_tagged_with_city():
    """Montgomery seed-file rows arrive tagged ``city='montgomery'``."""
    db_url, db_path = _fresh_async_db_url()
    try:
        engine = create_async_engine(db_url, echo=False)
        from app.core.database import init_db

        await init_db(engine)
        async with engine.begin() as conn:
            res = await conn.execute(text(
                "SELECT name, city FROM resources WHERE city = 'montgomery'"
            ))
            rows = res.fetchall()
        await engine.dispose()
        names = {row[0] for row in rows}
        # Pull from the legacy montgomery seed bundle.
        assert "Montgomery Area Transit System (MATS), The M" in names
        assert "Alabama DHR Child Care Subsidy Program" in names
        for _name, city in rows:
            assert city == "montgomery"
    finally:
        os.unlink(db_path)


# ── Cycle 3: query filters by per-request city context ───────────


@pytest.mark.asyncio
async def test_query_resources_filters_by_fort_worth_context():
    """When city context = fort-worth, query returns only FW rows."""
    db_url, db_path = _fresh_async_db_url()
    try:
        from sqlalchemy.ext.asyncio import async_sessionmaker
        from app.cities.config import clear_city_context, set_city_context
        from app.core.database import init_db
        from app.modules.matching.engine import query_resources_for_barriers
        from app.modules.matching.types import BarrierType

        engine = create_async_engine(db_url, echo=False)
        await init_db(engine)
        sm = async_sessionmaker(engine, expire_on_commit=False)
        try:
            set_city_context("fort-worth")
            async with sm() as session:
                rs = await query_resources_for_barriers(
                    [BarrierType.TRANSPORTATION, BarrierType.CHILDCARE],
                    session,
                )
            names = [r.name for r in rs]
            # Fort Worth specific present
            assert any("Trinity Metro" in n for n in names), names
            # No Montgomery / Alabama leaks
            for n in names:
                lower = n.lower()
                assert "montgomery" not in lower, f"AL leak: {n}"
                assert "alabama" not in lower, f"AL leak: {n}"
                assert "mats" not in lower, f"AL leak: {n}"
                assert "dhr" not in lower, f"AL leak: {n}"
        finally:
            clear_city_context()
            await engine.dispose()
    finally:
        os.unlink(db_path)


@pytest.mark.asyncio
async def test_query_resources_filters_by_montgomery_context():
    """When city context = montgomery, query returns only AL rows."""
    db_url, db_path = _fresh_async_db_url()
    try:
        from sqlalchemy.ext.asyncio import async_sessionmaker
        from app.cities.config import clear_city_context, set_city_context
        from app.core.database import init_db
        from app.modules.matching.engine import query_resources_for_barriers
        from app.modules.matching.types import BarrierType

        engine = create_async_engine(db_url, echo=False)
        await init_db(engine)
        sm = async_sessionmaker(engine, expire_on_commit=False)
        try:
            set_city_context("montgomery")
            async with sm() as session:
                rs = await query_resources_for_barriers(
                    [BarrierType.TRANSPORTATION, BarrierType.CHILDCARE],
                    session,
                )
            names = [r.name for r in rs]
            assert any("MATS" in n or "Montgomery" in n for n in names), names
            # No Fort Worth / Texas leaks.
            for n in names:
                lower = n.lower()
                assert "trinity metro" not in lower, f"TX leak: {n}"
                assert "tarrant" not in lower, f"TX leak: {n}"
                assert "fort worth" not in lower, f"TX leak: {n}"
                assert "texas" not in lower, f"TX leak: {n}"
        finally:
            clear_city_context()
            await engine.dispose()
    finally:
        os.unlink(db_path)


@pytest.mark.asyncio
async def test_seeder_loads_BOTH_cities_into_same_db():
    """A single startup should seed every city's resources.json into one DB.

    Without this, switching CITY=fort-worth at the env level loses every
    Alabama resource.  Both must coexist with city tags so per-request
    filtering picks the right slice at query time.
    """
    db_url, db_path = _fresh_async_db_url()
    try:
        engine = create_async_engine(db_url, echo=False)
        from app.core.database import init_db

        await init_db(engine)
        async with engine.begin() as conn:
            res = await conn.execute(text(
                "SELECT city, COUNT(*) FROM resources GROUP BY city"
            ))
            counts = dict(res.fetchall())
        await engine.dispose()
        assert counts.get("fort-worth", 0) >= 5
        assert counts.get("montgomery", 0) >= 5
    finally:
        os.unlink(db_path)

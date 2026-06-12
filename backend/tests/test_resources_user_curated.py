"""Tests for ``resources.user_curated_at`` (T26.1).

Three concerns covered here:

1. **Schema migration (0015)** — the column exists after alembic
   upgrade head, is nullable (no default), and adding it does not
   break legacy INSERTs that omit it.
2. **Migration idempotency** — re-running ``alembic upgrade head``
   on an already-upgraded DB is a no-op and does not error.
3. **Seed-loader respect** — ``seed_from_file`` skips upserting a
   row whose existing DB row has ``user_curated_at IS NOT NULL``.
   Default-NULL rows continue to seed normally so legacy single-city
   tests pass unchanged.

The seeder contract owned by T26.1 is "preserve admin edits". T26.2
will own the inverse half — every admin INSERT/UPDATE stamps
``user_curated_at = now()``. The two together close the loop where
re-seeding on container restart would clobber the admin's manual
curation.
"""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


# ── helpers ────────────────────────────────────────────────────────


def _backend_dir() -> Path:
    return Path(__file__).resolve().parent.parent


def _run_alembic_upgrade(db_path: str) -> None:
    backend = _backend_dir()
    alembic_bin = backend / ".venv" / "bin" / "alembic"
    env = os.environ.copy()
    env["DATABASE_URL"] = f"sqlite+aiosqlite:///{db_path}"
    subprocess.run(
        [str(alembic_bin), "upgrade", "head"],
        cwd=str(backend),
        env=env,
        check=True,
        capture_output=True,
    )


@pytest.fixture
def alembic_available() -> bool:
    backend = _backend_dir()
    alembic_bin = backend / ".venv" / "bin" / "alembic"
    if not alembic_bin.exists():
        pytest.skip("alembic binary not found in backend/.venv")
    if not (backend / "alembic" / "versions").exists():
        pytest.skip("alembic versions/ dir missing")
    return True


# ── 1. Schema migration ────────────────────────────────────────────


def test_user_curated_at_column_exists_after_alembic_upgrade(
    tmp_path, alembic_available
):
    """``alembic upgrade head`` creates ``resources.user_curated_at``."""
    db_path = str(tmp_path / "head.db")
    _run_alembic_upgrade(db_path)
    conn = sqlite3.connect(db_path)
    try:
        rows = list(conn.execute("PRAGMA table_info(resources)"))
    finally:
        conn.close()
    cols = {row[1]: row for row in rows}
    assert "user_curated_at" in cols, (
        f"resources.user_curated_at missing after upgrade; cols={list(cols)}"
    )
    # PRAGMA table_info row schema:
    # (cid, name, type, notnull, dflt_value, pk)
    info = cols["user_curated_at"]
    notnull = info[3]
    default = info[4]
    assert notnull == 0, "user_curated_at must be nullable (no NOT NULL)"
    assert default is None, (
        f"user_curated_at must have no DEFAULT; got {default!r}"
    )


def test_legacy_resources_insert_without_user_curated_still_works(
    tmp_path, alembic_available
):
    """Inserts that omit ``user_curated_at`` continue to succeed.

    Default-NULL preserves legacy single-city behaviour: existing
    seed/INSERT paths that do not know about the column still work.
    """
    db_path = str(tmp_path / "legacy_insert.db")
    _run_alembic_upgrade(db_path)
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO resources (name, category) VALUES (?, ?)",
            ("Legacy Resource", "social_service"),
        )
        conn.commit()
        row = conn.execute(
            "SELECT name, user_curated_at FROM resources "
            "WHERE name = 'Legacy Resource'"
        ).fetchone()
    finally:
        conn.close()
    assert row[0] == "Legacy Resource"
    assert row[1] is None, (
        f"omitted user_curated_at should default to NULL, got {row[1]!r}"
    )


def test_alembic_upgrade_is_idempotent(tmp_path, alembic_available):
    """Re-running ``alembic upgrade head`` on an upgraded DB is a no-op."""
    db_path = str(tmp_path / "idem.db")
    _run_alembic_upgrade(db_path)
    # Second run must not raise — alembic's version-tracking handles
    # the no-op case natively.
    _run_alembic_upgrade(db_path)
    conn = sqlite3.connect(db_path)
    try:
        cols = {
            row[1] for row in conn.execute("PRAGMA table_info(resources)")
        }
    finally:
        conn.close()
    assert "user_curated_at" in cols


# ── 2. Seed-loader respect ─────────────────────────────────────────


def _alembic_engine(db_path: str, alembic_available: bool):
    """Run alembic upgrade head and return an async engine."""
    _run_alembic_upgrade(db_path)
    db_url = f"sqlite+aiosqlite:///{db_path}"
    return create_async_engine(db_url, echo=False)


async def _seed_one_resource(
    engine, seed_path: Path, payload: dict, city_slug: str,
) -> None:
    """Write *payload* to *seed_path* and run seed_from_file in *city_slug*."""
    from app.core.seed_helpers import seed_from_file

    seed_path.write_text(json.dumps([payload]))
    async with engine.begin() as conn:
        await seed_from_file(
            conn, seed_path, "resources", city_slug=city_slug,
        )


async def _insert_resource(engine, **cols) -> None:
    """Insert one row into ``resources`` using the provided column dict."""
    columns = ", ".join(cols.keys())
    placeholders = ", ".join(f":{k}" for k in cols.keys())
    async with engine.begin() as conn:
        await conn.execute(text(
            f"INSERT INTO resources ({columns}) VALUES ({placeholders})"
        ), cols)


@pytest.mark.asyncio
async def test_seed_from_file_skips_user_curated_row(
    tmp_path, alembic_available
):
    """Pre-existing curated row (``user_curated_at IS NOT NULL``) is preserved.

    Curated row stays untouched and the seed row is dropped — count
    stays at 1, url remains ``admin-edit``.
    """
    db_path = str(tmp_path / "respect.db")
    engine = _alembic_engine(db_path, alembic_available)
    try:
        await _insert_resource(
            engine,
            name="Curated Place", category="social_service",
            city="montgomery", url="admin-edit",
            user_curated_at="2026-05-09T00:00:00",
        )
        await _seed_one_resource(
            engine, tmp_path / "curated_seed.json",
            {"name": "Curated Place", "category": "social_service",
             "url": "seed-default"},
            city_slug="montgomery",
        )
        async with engine.begin() as conn:
            res = await conn.execute(text(
                "SELECT url FROM resources "
                "WHERE city = 'montgomery' AND name = 'Curated Place'"
            ))
            urls = [row[0] for row in res.fetchall()]
    finally:
        await engine.dispose()
    assert urls == ["admin-edit"], (
        f"expected curated url preserved, got {urls!r}"
    )


@pytest.mark.asyncio
async def test_seed_from_file_does_not_skip_when_user_curated_at_is_null(
    tmp_path, alembic_available,
):
    """Rows where ``user_curated_at IS NULL`` are NOT skipped.

    Default-NULL rows keep the legacy seed semantics: every JSON entry
    is inserted on every seed pass. This is what makes existing
    single-city seed tests pass unchanged.
    """
    db_path = str(tmp_path / "null_curated.db")
    engine = _alembic_engine(db_path, alembic_available)
    try:
        await _insert_resource(
            engine, name="Plain Place", category="social_service",
            city="montgomery",
        )
        await _seed_one_resource(
            engine, tmp_path / "plain_seed.json",
            {"name": "Plain Place", "category": "social_service",
             "url": "seed-default"},
            city_slug="montgomery",
        )
        async with engine.begin() as conn:
            res = await conn.execute(text(
                "SELECT COUNT(*) FROM resources "
                "WHERE city = 'montgomery' AND name = 'Plain Place'"
            ))
            count = res.fetchone()[0]
    finally:
        await engine.dispose()
    # Original row + seed row both exist (no skip because curated IS NULL).
    assert count == 2, f"expected 2 rows (no skip on NULL), got {count}"


@pytest.mark.asyncio
async def test_seed_from_file_skip_is_per_city(tmp_path, alembic_available):
    """A curated row in city A does not block seeding in city B.

    The match key is ``(city, name)`` — same name in a different city
    must still seed. Otherwise an admin curating "Workforce Solutions"
    in fort-worth would silently block the same name from being
    seeded in dallas.
    """
    from app.core.seed_helpers import seed_from_file

    db_path = str(tmp_path / "per_city.db")
    engine = _alembic_engine(db_path, alembic_available)
    try:
        async with engine.begin() as conn:
            await conn.execute(text(
                "INSERT INTO resources "
                "(name, category, city, user_curated_at) "
                "VALUES (:n, :c, :ct, :t)"
            ), {
                "n": "Shared Name",
                "c": "social_service",
                "ct": "fort-worth",
                "t": "2026-05-09T00:00:00",
            })

        seed_data = [{
            "name": "Shared Name",
            "category": "social_service",
            "url": "dallas-default",
        }]
        seed_file = tmp_path / "shared_seed.json"
        seed_file.write_text(json.dumps(seed_data))

        async with engine.begin() as conn:
            await seed_from_file(
                conn, seed_file, "resources", city_slug="dallas",
            )

        async with engine.begin() as conn:
            res = await conn.execute(text(
                "SELECT city FROM resources "
                "WHERE name = 'Shared Name' ORDER BY city"
            ))
            cities = sorted(row[0] for row in res.fetchall())
    finally:
        await engine.dispose()

    assert cities == ["dallas", "fort-worth"], (
        f"expected dallas + fort-worth rows, got {cities!r}"
    )


@pytest.mark.asyncio
async def test_seed_from_file_non_resources_table_unaffected(
    tmp_path, alembic_available,
):
    """The skip logic is scoped to ``resources`` only.

    Other tables (e.g. employers) do not have the ``user_curated_at``
    column and must continue inserting every seed row unconditionally.
    """
    from app.core.seed_helpers import seed_from_file

    db_path = str(tmp_path / "other_table.db")
    engine = _alembic_engine(db_path, alembic_available)
    try:
        seed_data = [{
            "name": "Acme Co",
            "address": "123 Main St",
        }]
        seed_file = tmp_path / "employers.json"
        seed_file.write_text(json.dumps(seed_data))

        async with engine.begin() as conn:
            await seed_from_file(conn, seed_file, "employers")

        async with engine.begin() as conn:
            res = await conn.execute(text(
                "SELECT COUNT(*) FROM employers WHERE name = 'Acme Co'"
            ))
            count = res.fetchone()[0]
    finally:
        await engine.dispose()

    assert count == 1, f"expected employer seed insert, got {count}"

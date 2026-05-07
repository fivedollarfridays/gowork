"""Shared test fixtures for backend tests.

Dual-engine support (T22.2 + T23.9)
-----------------------------------
The ``db_engine`` fixture is parameterized over the configured engines:

* ``sqlite`` axis runs always (default local dev / CI).
* ``postgres`` axis runs only when ``GOWORK_TEST_POSTGRES_URL`` is set
  in the environment. Set it to a reachable
  ``postgresql+asyncpg://...`` URL.

Postgres axis isolation (T23.9)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The postgres axis was originally torn down with ``DROP SCHEMA public
CASCADE`` between every test, which lost races against pooled
connections in CI ("table already exists" / "constraint already
exists" on second run). T23.9 replaces that with a transaction-per-
test pattern:

* ``_postgres_engine_with_schema`` is a session-scoped fixture that
  builds the engine *once* and applies the alembic chain *once* per
  pytest session.
* ``db_engine`` (per-test, postgres axis) opens a connection on that
  engine, BEGINs an outer transaction, yields a connection that quacks
  like an engine for the existing ``async with db_engine.begin() as
  conn`` / ``async_sessionmaker(db_engine, ...)`` patterns, then
  ROLLBACKs at teardown — every test's writes are reverted with no
  schema-level churn.

The yielded object is a slot-compatible subclass of ``AsyncConnection``
(swapped in via ``__class__`` assignment) that overrides ``begin()`` to
yield the connection itself inside a SAVEPOINT, exposes a ``.url``
property, and a ``.connect()`` method — keeping the existing test
call sites working unchanged.

To run the suite against postgres locally::

    GOWORK_TEST_POSTGRES_URL=postgresql+asyncpg://localhost/montgowork_test \
        pytest backend/tests
"""

from __future__ import annotations

import contextlib
import os
from typing import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncConnection, create_async_engine

from app.barrier_graph.seed import upsert_barrier_graph
from app.core import database as db_module
from app.core.config import get_settings
from app.core.database import get_async_session_factory, init_db
from app.core.db_url import normalize_async_url

#: Env var that opts in to the postgres test axis. Documented above.
POSTGRES_TEST_URL_ENV_VAR = "GOWORK_TEST_POSTGRES_URL"


def _db_engine_params() -> list:
    """Return the ``pytest.param`` list for the ``db_engine`` fixture.

    Always includes a sqlite axis; conditionally adds a postgres axis
    when ``GOWORK_TEST_POSTGRES_URL`` is set.
    """
    params = [pytest.param("sqlite", id="sqlite")]
    if os.environ.get(POSTGRES_TEST_URL_ENV_VAR):
        params.append(pytest.param("postgres", id="postgres"))
    return params


@pytest.fixture(autouse=True)
def _pin_city_to_montgomery_for_tests(monkeypatch):
    """Pin CITY=montgomery for the test suite.

    Production default flipped to "fort-worth" (the active reference
    deployment for HackFW), but the test suite — seed data, fixtures,
    helpers, and most assertions — was written against Montgomery.
    Pinning the env var here keeps every legacy assertion green without
    rewriting ~99 tests, while production stays on Fort Worth.

    Tests that need to verify the bare default value (no env var) use
    `monkeypatch.delenv("CITY", raising=False)` themselves; this fixture
    runs first but those tests then override.
    """
    monkeypatch.setenv("CITY", "montgomery")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture(scope="session")
def anyio_backend():
    """Session-scoped anyio backend.

    Promoted from function-scoped (the original) to session-scoped in
    T23.9 so session-scoped async fixtures (like
    ``_postgres_engine_with_schema``) can transitively depend on it
    without a ScopeMismatch error. The semantic is unchanged — every
    test still runs on the asyncio backend.
    """
    return "asyncio"


@pytest.fixture
async def test_engine(tmp_path):
    """Create a fresh SQLite engine pointing at a temp directory.

    Clears get_settings lru_cache and resets the _engine global
    so no test ever touches the production database.
    """
    get_settings.cache_clear()

    db_path = tmp_path / "test.db"
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{db_path}",
        echo=False,
    )
    old_engine = db_module._engine
    old_factory = db_module._async_session_factory
    db_module._engine = engine
    db_module._async_session_factory = None

    await init_db(engine)

    factory = get_async_session_factory()
    async with factory() as session:
        await upsert_barrier_graph(session)

    yield engine

    await engine.dispose()
    db_module._engine = old_engine
    db_module._async_session_factory = old_factory


@pytest.fixture
async def client(test_engine):
    """Async test client that uses the test_engine fixture."""
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ---------------------------------------------------------------------------
# Postgres axis: session-scoped engine + per-test transaction-rollback (T23.9)
# ---------------------------------------------------------------------------


class _PgFixtureConnection(AsyncConnection):
    """``AsyncConnection`` subclass yielded as ``db_engine`` on postgres axis.

    Same slots as the parent (no extra state), so an existing
    ``AsyncConnection`` can be promoted via ``conn.__class__ =
    _PgFixtureConnection`` without re-initialisation.

    Why a class swap instead of a wrapper class?
        Tests pass ``db_engine`` directly to ``async_sessionmaker(...)``
        and SQLAlchemy's bind resolver dispatches on
        ``isinstance(bind, AsyncConnection)``. A wrapper class would
        miss that dispatch and the session would create fresh
        connections from the engine, bypassing the outer transaction.
        Promoting the live ``AsyncConnection`` keeps ``isinstance``
        true and ``_proxied`` returning the in-tx sync ``Connection``
        so ``session.commit()`` lands inside our outer transaction
        (autobegin → SAVEPOINT under SQLAlchemy 2.0's default
        ``join_transaction_mode``).

    Surface added on top of ``AsyncConnection``:
        * ``begin()`` — yields *self* inside a SAVEPOINT (matches the
          ``async with engine.begin() as conn`` idiom).
        * ``connect()`` — yields *self* (matches the
          ``async with engine.connect() as conn`` idiom).
        * ``url`` — proxies to the underlying engine URL (matches
          ``db_engine.url.drivername`` test sites).
    """

    __slots__ = ()

    @contextlib.asynccontextmanager
    async def begin(self) -> AsyncIterator["_PgFixtureConnection"]:
        """Engine-style begin: yield self inside a SAVEPOINT.

        The outer fixture has already opened a real transaction on this
        connection; nesting a SAVEPOINT here gives test code its own
        sub-scope. On exit the savepoint is released (or rolled back on
        exception) and the outer transaction continues — until the
        fixture's teardown rolls *that* back too.
        """
        async with self.begin_nested():
            yield self

    @contextlib.asynccontextmanager
    async def connect(self) -> AsyncIterator["_PgFixtureConnection"]:
        """Engine-style connect: yield self (no nested transaction).

        Some tests use ``async with engine.connect() as conn`` for
        read-only queries; a no-op context manager preserves that idiom
        without opening a savepoint we don't need.
        """
        yield self

    @property
    def url(self):
        """Proxy to the underlying engine's URL (for ``.url.drivername``)."""
        return self.engine.url


@pytest.fixture(scope="session")
async def _postgres_engine_with_schema():
    """Session-scoped postgres engine with the alembic chain pre-applied.

    Created once at the start of the pytest session, used by every
    postgres-axis ``db_engine`` invocation. Schema is applied via the
    alembic chain (dialect-aware via ``legacy_ddl_translator``);
    teardown drops ``public`` so the next session starts clean.

    Skipped (yields ``None``) when ``GOWORK_TEST_POSTGRES_URL`` is unset
    so the sqlite-only default flow doesn't touch postgres at all.
    """
    raw = os.environ.get(POSTGRES_TEST_URL_ENV_VAR)
    if not raw:
        yield None
        return

    url = normalize_async_url(raw)
    engine = create_async_engine(url, echo=False)
    await _bootstrap_postgres_schema_via_alembic(engine)
    try:
        yield engine
    finally:
        await _teardown_postgres_schema(engine)
        await engine.dispose()


@pytest.fixture(params=_db_engine_params())
async def db_engine(request, tmp_path, _postgres_engine_with_schema):
    """Parameterized async engine, exercises sqlite + (opt-in) postgres.

    Sqlite axis (default): per-test ``tmp_path`` file, full ``init_db``
    chain + barrier-graph seed. Engine is disposed at teardown.

    Postgres axis (opt-in via ``GOWORK_TEST_POSTGRES_URL``, T23.9):
    reuses the session-scoped engine, opens a connection, BEGINs an
    outer transaction, yields a class-swapped ``_PgFixtureConnection``
    so existing ``async with db_engine.begin()`` / sessionmaker call
    sites keep working. ROLLBACKs the outer transaction on teardown so
    every test sees a pristine database — no DROP SCHEMA, no race
    against pooled connections.
    """
    if request.param == "sqlite":
        async for engine in _sqlite_axis_engine(tmp_path):
            yield engine
        return

    engine = _postgres_engine_with_schema
    assert engine is not None, (
        "postgres axis requested but session-scoped engine fixture "
        "yielded None — env var resolution drift?"
    )
    async for db in _postgres_axis_connection(engine):
        yield db


async def _sqlite_axis_engine(tmp_path) -> AsyncIterator:
    """Sqlite-axis ``db_engine`` body: per-test temp file, full init_db."""
    url = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"
    engine = create_async_engine(url, echo=False)
    old_engine = db_module._engine
    old_factory = db_module._async_session_factory
    db_module._engine = engine
    db_module._async_session_factory = None

    # init_db replays the legacy DDL_SQL blob (m001 baseline) +
    # apply_pending_migrations + seed. Sqlite-only path: the blob
    # contains AUTOINCREMENT and PRAGMA statements that postgres
    # rejects, and the legacy chain has no dialect translator.
    await init_db(engine)
    try:
        yield engine
    finally:
        await engine.dispose()
        db_module._engine = old_engine
        db_module._async_session_factory = old_factory


async def _postgres_axis_connection(engine) -> AsyncIterator[_PgFixtureConnection]:
    """Postgres-axis ``db_engine`` body: in-tx connection, rollback on exit."""
    old_engine = db_module._engine
    old_factory = db_module._async_session_factory
    db_module._engine = engine
    db_module._async_session_factory = None

    raw_conn = await engine.connect()
    try:
        outer_trans = await raw_conn.begin()
        # Promote the live AsyncConnection to our subclass so begin()
        # / connect() / url overrides apply for the test's lifetime.
        raw_conn.__class__ = _PgFixtureConnection
        try:
            yield raw_conn  # type: ignore[misc]  # class is now subclass
        finally:
            # Demote before rollback so the parent's begin() semantics
            # apply for transaction control (avoid recursing into the
            # subclass override).
            raw_conn.__class__ = AsyncConnection
            await outer_trans.rollback()
    finally:
        await raw_conn.close()
        db_module._engine = old_engine
        db_module._async_session_factory = old_factory


async def _bootstrap_postgres_schema_via_alembic(engine) -> None:
    """Apply the alembic chain to ``engine`` for the postgres test axis.

    Uses ``Config.attributes['connection']`` so alembic reuses the
    fixture's engine instead of opening its own from the env DATABASE_URL.
    """
    from pathlib import Path

    from alembic.config import Config

    cfg_path = Path(__file__).resolve().parent.parent / "alembic.ini"
    cfg = Config(str(cfg_path))
    cfg.set_main_option(
        "script_location",
        str(Path(__file__).resolve().parent.parent / "alembic"),
    )
    async with engine.begin() as conn:
        await conn.run_sync(
            lambda sync_conn: _run_alembic_upgrade(cfg, sync_conn)
        )


def _run_alembic_upgrade(cfg, sync_conn) -> None:
    """Run ``alembic upgrade head`` against ``sync_conn``.

    Alembic's command API is sync — used inside ``conn.run_sync`` so
    the async fixture stays driver-agnostic.
    """
    from alembic import command

    cfg.attributes["connection"] = sync_conn
    command.upgrade(cfg, "head")


async def _teardown_postgres_schema(engine) -> None:
    """Drop the ``public`` schema at session-end so the next session is clean.

    Per-test isolation is now via transaction-rollback (T23.9), so this
    runs once at the end of the pytest session — there's no race with
    pooled connections because no further tests run after teardown.
    """
    async with engine.begin() as conn:
        await conn.exec_driver_sql("DROP SCHEMA public CASCADE")
        await conn.exec_driver_sql("CREATE SCHEMA public")

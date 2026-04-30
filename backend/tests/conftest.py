"""Shared test fixtures for backend tests."""

import os

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine

from app.barrier_graph.seed import upsert_barrier_graph
from app.core import database as db_module
from app.core.config import get_settings
from app.core.database import get_async_session_factory, init_db


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


@pytest.fixture
def anyio_backend():
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

"""Shared test fixtures for MontGoWork backend tests."""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine

from app.barrier_graph.seed import upsert_barrier_graph
from app.core import database as db_module
from app.core.config import get_settings
from app.core.database import get_async_session_factory, init_db


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

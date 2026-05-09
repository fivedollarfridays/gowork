"""Shared fixtures + DB helpers for the T26.2 admin-resources test suite.

Lifted out of :mod:`tests.test_admin_resources` to keep the test file
under the architecture warning + error thresholds. The fixtures here
mount the T26.2 router on a fresh FastAPI app and layer the accounts +
roles DDL plus the 0015 ``user_curated_at`` column on top of
``test_engine`` so query helpers run end-to-end against the same
schema the deployment chain ships.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core import queries_accounts, queries_roles
from app.core.accounts_schema import apply_ddl as apply_accounts_ddl
from app.core.roles_schema import apply_ddl as apply_roles_ddl
from app.routes._auth_claim_helpers import build_account_cookie_value


async def ensure_user_curated_at(conn) -> None:
    """Add ``resources.user_curated_at`` if missing.

    The legacy sqlite migration runner used by ``test_engine`` stops at
    m010; the 0015 alembic revision (which adds this column on the
    deployment chain) isn't applied to the test engine. Mirror the
    alembic migration's idempotent ALTER so these tests can stand on
    the same column the deployment surface relies on without coupling
    to the alembic test bootstrap.
    """
    cols = await conn.execute(text("PRAGMA table_info(resources)"))
    if not any(row[1] == "user_curated_at" for row in cols.fetchall()):
        await conn.execute(
            text("ALTER TABLE resources ADD COLUMN user_curated_at TIMESTAMP")
        )


@pytest.fixture
async def resources_engine(test_engine):
    """test_engine + accounts + roles DDL + 0015 column applied on top."""
    async with test_engine.begin() as conn:
        await conn.run_sync(apply_accounts_ddl)
        await conn.run_sync(apply_roles_ddl)
        await ensure_user_curated_at(conn)
    return test_engine


@pytest.fixture
def session_factory(resources_engine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        resources_engine, class_=AsyncSession, expire_on_commit=False
    )


@pytest.fixture
async def admin_resources_client(resources_engine):
    """Fresh FastAPI app mounting only the T26.2 router.

    Decoupled from ``app.main.app`` because T26.2 also owns the
    ``routes/__init__.py`` registration this wave; mounting locally
    avoids depending on the global registration order.
    """
    from app.routes.admin_resources import router

    app = FastAPI()
    app.include_router(router)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def seed_admin(
    session: AsyncSession, email: str
) -> tuple[int, str]:
    """Create an account + grant 'admin' role; return (id, cookie_value)."""
    account_id = await queries_accounts.create_account(session, email=email)
    await queries_roles.grant_role(session, account_id, "admin")
    return account_id, build_account_cookie_value(account_id)


async def seed_non_admin(
    session: AsyncSession, email: str
) -> tuple[int, str]:
    """Create an account WITHOUT a role grant; return (id, cookie_value)."""
    account_id = await queries_accounts.create_account(session, email=email)
    return account_id, build_account_cookie_value(account_id)


async def seed_resource(
    session: AsyncSession,
    *,
    name: str,
    city: str = "fort-worth",
    health_status: str = "healthy",
    category: str = "social_service",
    user_curated_at: str | None = None,
) -> int:
    """Insert one resource row directly; returns the new id."""
    cols = ["name", "category", "city", "health_status"]
    binds: dict[str, object] = {
        "name": name, "category": category, "city": city,
        "health_status": health_status,
    }
    if user_curated_at is not None:
        cols.append("user_curated_at")
        binds["user_curated_at"] = user_curated_at
    placeholders = ", ".join(f":{c}" for c in cols)
    column_list = ", ".join(cols)
    result = await session.execute(
        text(
            f"INSERT INTO resources ({column_list}) "
            f"VALUES ({placeholders}) RETURNING id"
        ),
        binds,
    )
    rid = int(result.scalar_one())
    await session.commit()
    return rid


async def read_resource_row(
    session: AsyncSession, resource_id: int
) -> dict | None:
    """Read the resource row as a plain dict; ``None`` when absent."""
    result = await session.execute(
        text(
            "SELECT id, name, category, city, health_status, "
            "user_curated_at, address, lat, lng, phone, url "
            "FROM resources WHERE id = :id"
        ),
        {"id": resource_id},
    )
    row = result.first()
    if row is None:
        return None
    return dict(row._mapping)


__all__ = [
    "admin_resources_client",
    "ensure_user_curated_at",
    "read_resource_row",
    "resources_engine",
    "seed_admin",
    "seed_non_admin",
    "seed_resource",
    "session_factory",
]

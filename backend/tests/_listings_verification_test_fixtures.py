"""Shared fixtures + helpers for the T24.2 verification CRUD test suite.

Three test modules consume this:

* ``test_queries_employers.py`` — employer_accounts CRUD + the
  list_pending_admin_review join.
* ``test_queries_listings_verification.py`` — claim flow + verification
  CRUD + the public summary projection.
* ``test_queries_listings_reputation.py`` — record_event + the T24.8
  signal-rates stubs.

Splitting the test surface keeps each test file under the per-file
size limit; sharing the fixtures + helpers via this module keeps the
"same accounts/listings seed used everywhere" invariant. Filename
starts with an underscore so pytest does not treat it as a test
module.
"""

from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core import queries_accounts
from app.core.accounts_schema import apply_ddl as apply_accounts_ddl
from app.core.listings_verification_schema import (
    apply_ddl as apply_verification_ddl,
)


@pytest.fixture
async def verification_engine(db_engine):
    """``db_engine`` plus accounts + verification DDL applied on top."""
    async with db_engine.begin() as conn:
        await conn.run_sync(apply_accounts_ddl)
        await conn.run_sync(apply_verification_ddl)
    return db_engine


@pytest.fixture
def session_factory(verification_engine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        verification_engine, class_=AsyncSession, expire_on_commit=False
    )


async def make_account(session: AsyncSession, email: str) -> int:
    """Create one account row, return its id (delegates to queries_accounts)."""
    return await queries_accounts.create_account(session, email=email)


async def make_listing(session: AsyncSession, *, title: str) -> int:
    """Insert one row into the legacy job_listings table, return id."""
    result = await session.execute(
        text(
            "INSERT INTO job_listings (title, scraped_at) "
            "VALUES (:title, :scraped_at) RETURNING id"
        ),
        {"title": title, "scraped_at": "2026-05-08T00:00:00Z"},
    )
    new_id = int(result.scalar_one())
    await session.commit()
    return new_id


__all__ = [
    "verification_engine",
    "session_factory",
    "make_account",
    "make_listing",
]

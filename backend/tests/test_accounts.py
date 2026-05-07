"""Tests for the identity layer (T22.5).

Covers the three new tables — ``accounts``, ``account_sessions``,
``account_credentials`` — and the CRUD surface in
:mod:`app.core.queries_accounts`.

Schema strategy
---------------
The ``db_engine`` fixture (T22.2) only runs the legacy m001..m010 DDL
via the sync runner; it does not yet apply alembic 0011. To exercise
the identity tables on top of the existing schema we apply the
accounts DDL on demand through :func:`app.core.accounts_schema.apply_ddl`,
which is also what the alembic 0011 revision uses. This keeps the test
hermetic and dialect-portable: the same DDL ships in both code paths.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core import queries_accounts
from app.core.accounts_schema import apply_ddl


@pytest.fixture
async def accounts_engine(db_engine):
    """``db_engine`` plus the identity-layer DDL applied on top."""
    async with db_engine.begin() as conn:
        await conn.run_sync(apply_ddl)
    return db_engine


@pytest.fixture
def session_factory(accounts_engine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        accounts_engine, class_=AsyncSession, expire_on_commit=False
    )


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _make_session_row(session: AsyncSession, sid: str) -> None:
    """Insert a minimal sessions row with the required NOT NULL columns."""
    now = _utcnow_iso()
    expires = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    await session.execute(
        text(
            "INSERT INTO sessions (id, created_at, barriers, expires_at) "
            "VALUES (:id, :created_at, :barriers, :expires_at)"
        ),
        {"id": sid, "created_at": now, "barriers": "[]", "expires_at": expires},
    )
    await session.commit()


@pytest.mark.anyio
async def test_create_account_returns_id_and_persists_email(session_factory):
    """create_account inserts a row and returns its primary key."""
    async with session_factory() as session:
        account_id = await queries_accounts.create_account(
            session, email="alice@example.com"
        )
        assert isinstance(account_id, int)
        assert account_id > 0

        result = await session.execute(
            text("SELECT email FROM accounts WHERE id = :id"),
            {"id": account_id},
        )
        row = result.first()
        assert row is not None
        assert row._mapping["email"] == "alice@example.com"


@pytest.mark.anyio
async def test_create_account_normalizes_email(session_factory):
    """Email lookup is case-insensitive: stored lowercased + trimmed."""
    async with session_factory() as session:
        await queries_accounts.create_account(session, email="  Bob@Example.COM ")
        found = await queries_accounts.get_account_by_email(
            session, "bob@example.com"
        )
        assert found is not None
        assert found["email"] == "bob@example.com"


@pytest.mark.anyio
async def test_get_account_by_email_returns_none_when_missing(session_factory):
    """Lookup of a never-created email returns None."""
    async with session_factory() as session:
        found = await queries_accounts.get_account_by_email(
            session, "ghost@example.com"
        )
        assert found is None


@pytest.mark.anyio
async def test_create_account_unique_email(session_factory):
    """Inserting the same email twice must raise an integrity error."""
    async with session_factory() as session:
        await queries_accounts.create_account(session, email="dup@example.com")
        with pytest.raises(Exception):  # IntegrityError on either dialect
            await queries_accounts.create_account(session, email="dup@example.com")


@pytest.mark.anyio
async def test_claim_session_links_account_to_session(session_factory):
    """claim_session inserts into account_sessions and is idempotent."""
    async with session_factory() as session:
        account_id = await queries_accounts.create_account(
            session, email="carol@example.com"
        )
        await _make_session_row(session, "sess-1")

        await queries_accounts.claim_session(session, account_id, "sess-1")
        # Idempotent: second call on the same (account, session) is a noop.
        await queries_accounts.claim_session(session, account_id, "sess-1")

        rows = await queries_accounts.list_sessions_for_account(session, account_id)
        assert rows == ["sess-1"]


@pytest.mark.anyio
async def test_session_belongs_to_at_most_one_account(session_factory):
    """UNIQUE(session_id) — claiming a session for a 2nd account fails."""
    async with session_factory() as session:
        a1 = await queries_accounts.create_account(session, email="a1@example.com")
        a2 = await queries_accounts.create_account(session, email="a2@example.com")
        await _make_session_row(session, "shared-sess")

        await queries_accounts.claim_session(session, a1, "shared-sess")
        with pytest.raises(Exception):
            await queries_accounts.claim_session(session, a2, "shared-sess")


@pytest.mark.anyio
async def test_list_sessions_for_account_returns_all_claimed(session_factory):
    """An account can claim many sessions; list returns all of them."""
    async with session_factory() as session:
        account_id = await queries_accounts.create_account(
            session, email="dave@example.com"
        )
        for sid in ("s-a", "s-b", "s-c"):
            await _make_session_row(session, sid)
            await queries_accounts.claim_session(session, account_id, sid)

        rows = await queries_accounts.list_sessions_for_account(session, account_id)
        assert sorted(rows) == ["s-a", "s-b", "s-c"]


@pytest.mark.anyio
async def test_list_sessions_for_account_empty_for_unknown(session_factory):
    """Unknown account returns []."""
    async with session_factory() as session:
        rows = await queries_accounts.list_sessions_for_account(session, 99999)
        assert rows == []


@pytest.mark.anyio
async def test_get_account_for_session_returns_owner(session_factory):
    """get_account_for_session round-trips after claim_session."""
    async with session_factory() as session:
        account_id = await queries_accounts.create_account(
            session, email="eve@example.com"
        )
        await _make_session_row(session, "owned-sess")
        await queries_accounts.claim_session(session, account_id, "owned-sess")

        owner = await queries_accounts.get_account_for_session(session, "owned-sess")
        assert owner is not None
        assert owner["id"] == account_id
        assert owner["email"] == "eve@example.com"


@pytest.mark.anyio
async def test_get_account_for_session_returns_none_when_unclaimed(session_factory):
    """A session never claimed returns None (anonymous-first invariant)."""
    async with session_factory() as session:
        await _make_session_row(session, "anon-sess")
        owner = await queries_accounts.get_account_for_session(session, "anon-sess")
        assert owner is None


@pytest.mark.anyio
async def test_account_credentials_table_exists_and_accepts_inserts(
    session_factory,
):
    """account_credentials accepts a magic_link row with hash + expiry."""
    async with session_factory() as session:
        account_id = await queries_accounts.create_account(
            session, email="frank@example.com"
        )
        expires = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        await session.execute(
            text(
                "INSERT INTO account_credentials "
                "(account_id, credential_type, credential_value_hash, expires_at) "
                "VALUES (:aid, :ct, :hash, :exp)"
            ),
            {
                "aid": account_id,
                "ct": "magic_link",
                "hash": "a" * 64,
                "exp": expires,
            },
        )
        await session.commit()

        result = await session.execute(
            text(
                "SELECT credential_type, used_at FROM account_credentials "
                "WHERE account_id = :aid"
            ),
            {"aid": account_id},
        )
        row = result.first()
        assert row is not None
        assert row._mapping["credential_type"] == "magic_link"
        assert row._mapping["used_at"] is None

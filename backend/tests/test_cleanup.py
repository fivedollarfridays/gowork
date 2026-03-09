"""Tests for expired session cleanup."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text

from app.core.cleanup import cleanup_expired_sessions
from app.core.database import get_async_session_factory


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def _insert_session(factory, sid: str, expires_at: datetime) -> None:
    async with factory() as session:
        await session.execute(
            text(
                "INSERT INTO sessions (id, created_at, barriers, expires_at) "
                "VALUES (:id, :ca, :b, :ea)"
            ),
            {"id": sid, "ca": _iso(_now()), "b": "[]", "ea": _iso(expires_at)},
        )
        await session.commit()


async def _insert_related_data(factory, sid: str) -> None:
    """Insert one row into each session-related table."""
    now = _iso(_now())
    async with factory() as session:
        await session.execute(
            text("INSERT INTO feedback_tokens (token, session_id, created_at, expires_at) VALUES (:t, :sid, :ca, :ea)"),
            {"t": "tok-1", "sid": sid, "ca": now, "ea": _iso(_now() + timedelta(days=1))},
        )
        await session.execute(
            text("INSERT INTO visit_feedback (session_id, submitted_at, made_it_to_center, plan_accuracy) VALUES (:sid, :sa, :m, :pa)"),
            {"sid": sid, "sa": now, "m": 1, "pa": 4},
        )
        await session.execute(
            text("INSERT INTO resource_feedback (resource_id, session_id, helpful, submitted_at) VALUES (:rid, :sid, :h, :sa)"),
            {"rid": 1, "sid": sid, "h": 1, "sa": now},
        )
        await session.execute(
            text("INSERT INTO record_profiles (session_id, record_types, charge_categories, years_since_conviction, completed_sentence) VALUES (:sid, :rt, :cc, :ysc, :cs)"),
            {"sid": sid, "rt": "[]", "cc": "[]", "ysc": 5, "cs": 1},
        )
        await session.commit()


async def _assert_session_exists(factory, sid: str, exists: bool) -> None:
    async with factory() as session:
        result = await session.execute(
            text("SELECT id FROM sessions WHERE id = :sid"), {"sid": sid},
        )
        if exists:
            assert result.first() is not None
        else:
            assert result.first() is None


class TestCleanupExpiredSessions:
    @pytest.mark.anyio
    async def test_deletes_expired_session(self, test_engine):
        """Sessions expired >48h ago are deleted."""
        factory = get_async_session_factory()
        await _insert_session(factory, "expired-1", _now() - timedelta(hours=49))

        async with factory() as session:
            count = await cleanup_expired_sessions(session)

        assert count == 1
        await _assert_session_exists(factory, "expired-1", False)

    @pytest.mark.anyio
    async def test_preserves_non_expired_session(self, test_engine):
        """Sessions not yet expired are preserved."""
        factory = get_async_session_factory()
        await _insert_session(factory, "active-1", _now() + timedelta(days=5))

        async with factory() as session:
            count = await cleanup_expired_sessions(session)

        assert count == 0
        await _assert_session_exists(factory, "active-1", True)

    @pytest.mark.anyio
    async def test_preserves_recently_expired_session(self, test_engine):
        """Sessions expired <48h ago are preserved (grace period)."""
        factory = get_async_session_factory()
        await _insert_session(factory, "recent-1", _now() - timedelta(hours=24))

        async with factory() as session:
            count = await cleanup_expired_sessions(session)

        assert count == 0
        await _assert_session_exists(factory, "recent-1", True)

    @pytest.mark.anyio
    async def test_cascading_deletes(self, test_engine):
        """Deleting a session also deletes related data."""
        factory = get_async_session_factory()
        sid = "cascade-1"
        await _insert_session(factory, sid, _now() - timedelta(hours=49))
        await _insert_related_data(factory, sid)

        async with factory() as session:
            count = await cleanup_expired_sessions(session)
        assert count == 1

        tables = ("sessions", "feedback_tokens", "visit_feedback", "resource_feedback", "record_profiles")
        async with factory() as session:
            for table in tables:
                col = "id" if table == "sessions" else "session_id"
                result = await session.execute(
                    text(f"SELECT COUNT(*) FROM {table} WHERE {col} = :sid"),
                    {"sid": sid},
                )
                assert result.scalar() == 0, f"Expected 0 rows in {table}"

    @pytest.mark.anyio
    async def test_no_expired_sessions(self, test_engine):
        """Cleanup with no expired sessions returns 0."""
        factory = get_async_session_factory()
        async with factory() as session:
            count = await cleanup_expired_sessions(session)
        assert count == 0

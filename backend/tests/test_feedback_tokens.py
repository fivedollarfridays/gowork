"""Tests for feedback token generation and validation."""

import pytest

from app.modules.feedback.tokens import generate_token


class TestGenerateToken:
    def test_produces_url_safe_string(self):
        """Token should be URL-safe (alphanumeric, -, _)."""
        token = generate_token()
        assert all(c.isalnum() or c in "-_" for c in token)

    def test_under_20_chars(self):
        """Token should be < 20 chars."""
        token = generate_token()
        assert len(token) < 20

    def test_non_deterministic(self):
        """Each call produces a unique token."""
        t1 = generate_token()
        t2 = generate_token()
        assert t1 != t2

    def test_different_calls_different_tokens(self):
        """Consecutive calls always produce different tokens."""
        t1 = generate_token()
        t2 = generate_token()
        assert t1 != t2

    def test_nonempty(self):
        """Token should not be empty."""
        token = generate_token()
        assert len(token) > 0


class TestCreateAndValidateToken:
    @pytest.mark.anyio
    async def test_create_stores_token(self, test_engine):
        """create_feedback_token should store token in DB."""
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

        from app.core.queries_feedback import create_feedback_token

        factory = async_sessionmaker(test_engine, class_=AsyncSession)
        async with factory() as session:
            # First create a session row so FK-like constraints work
            await session.execute(text(
                "INSERT INTO sessions (id, created_at, barriers, expires_at) "
                "VALUES ('sess-1', '2026-03-05', '[]', '2026-04-05')"
            ))
            await session.commit()

            token = await create_feedback_token(session, "sess-1")
            assert token is not None
            assert len(token) > 0

    @pytest.mark.anyio
    async def test_validate_returns_session_id(self, test_engine):
        """validate_token should return session_id for valid token."""
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

        from app.core.queries_feedback import create_feedback_token, validate_token

        factory = async_sessionmaker(test_engine, class_=AsyncSession)
        async with factory() as session:
            await session.execute(text(
                "INSERT INTO sessions (id, created_at, barriers, expires_at) "
                "VALUES ('sess-2', '2026-03-05', '[]', '2026-04-05')"
            ))
            await session.commit()

            token = await create_feedback_token(session, "sess-2")
            result = await validate_token(session, token)
            assert result == "sess-2"

    @pytest.mark.anyio
    async def test_validate_returns_none_for_unknown(self, test_engine):
        """validate_token should return None for unknown tokens."""
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

        from app.core.queries_feedback import validate_token

        factory = async_sessionmaker(test_engine, class_=AsyncSession)
        async with factory() as session:
            result = await validate_token(session, "nonexistent-token")
            assert result is None

    @pytest.mark.anyio
    async def test_validate_returns_none_for_expired(self, test_engine):
        """validate_token should return None for expired tokens."""
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

        from app.core.queries_feedback import validate_token
        from app.modules.feedback.tokens import generate_token

        factory = async_sessionmaker(test_engine, class_=AsyncSession)
        async with factory() as session:
            token = generate_token()
            # Insert with already-expired date
            await session.execute(text(
                "INSERT INTO feedback_tokens (token, session_id, created_at, expires_at) "
                "VALUES (:token, 'sess-expired', '2026-01-01', '2026-01-02')"
            ), {"token": token})
            await session.commit()

            result = await validate_token(session, token)
            assert result is None

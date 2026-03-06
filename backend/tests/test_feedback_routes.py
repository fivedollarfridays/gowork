"""Tests for feedback routes — resource feedback endpoint."""

import pytest


class TestResourceFeedbackEndpoint:
    """POST /api/feedback/resource — one-tap resource feedback."""

    @pytest.mark.anyio
    async def test_valid_feedback_returns_200(self, client, test_engine):
        """Valid feedback submission returns success."""
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

        factory = async_sessionmaker(test_engine, class_=AsyncSession)
        async with factory() as session:
            await session.execute(text(
                "INSERT INTO sessions (id, created_at, barriers, expires_at) "
                "VALUES ('sess-fb-1', '2026-03-06', '[]', '2026-04-06')"
            ))
            await session.commit()

        resp = await client.post("/api/feedback/resource", json={
            "resource_id": 1,
            "session_id": "sess-fb-1",
            "helpful": True,
            "barrier_type": "credit",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["resource_id"] == 1
        assert data["helpful"] is True

    @pytest.mark.anyio
    async def test_feedback_without_barrier_type(self, client, test_engine):
        """Feedback without optional barrier_type is accepted."""
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

        factory = async_sessionmaker(test_engine, class_=AsyncSession)
        async with factory() as session:
            await session.execute(text(
                "INSERT INTO sessions (id, created_at, barriers, expires_at) "
                "VALUES ('sess-fb-2', '2026-03-06', '[]', '2026-04-06')"
            ))
            await session.commit()

        resp = await client.post("/api/feedback/resource", json={
            "resource_id": 2,
            "session_id": "sess-fb-2",
            "helpful": False,
        })
        assert resp.status_code == 200
        assert resp.json()["helpful"] is False

    @pytest.mark.anyio
    async def test_unknown_session_returns_404(self, client):
        """Feedback for non-existent session returns 404."""
        resp = await client.post("/api/feedback/resource", json={
            "resource_id": 1,
            "session_id": "nonexistent-session",
            "helpful": True,
        })
        assert resp.status_code == 404

    @pytest.mark.anyio
    async def test_upsert_updates_existing_vote(self, client, test_engine):
        """Re-voting on same resource+session updates instead of duplicating."""
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

        factory = async_sessionmaker(test_engine, class_=AsyncSession)
        async with factory() as session:
            await session.execute(text(
                "INSERT INTO sessions (id, created_at, barriers, expires_at) "
                "VALUES ('sess-fb-3', '2026-03-06', '[]', '2026-04-06')"
            ))
            await session.commit()

        # First vote: helpful
        resp1 = await client.post("/api/feedback/resource", json={
            "resource_id": 5,
            "session_id": "sess-fb-3",
            "helpful": True,
        })
        assert resp1.status_code == 200

        # Second vote: not helpful (should update, not duplicate)
        resp2 = await client.post("/api/feedback/resource", json={
            "resource_id": 5,
            "session_id": "sess-fb-3",
            "helpful": False,
        })
        assert resp2.status_code == 200
        assert resp2.json()["helpful"] is False

        # Verify only one row exists
        async with factory() as session:
            result = await session.execute(text(
                "SELECT COUNT(*) FROM resource_feedback "
                "WHERE resource_id = 5 AND session_id = 'sess-fb-3'"
            ))
            count = result.scalar()
            assert count == 1

            # Verify it's the updated value
            result = await session.execute(text(
                "SELECT helpful FROM resource_feedback "
                "WHERE resource_id = 5 AND session_id = 'sess-fb-3'"
            ))
            assert result.scalar() == 0  # False = 0

    @pytest.mark.anyio
    async def test_feedback_persisted_with_timestamp(self, client, test_engine):
        """Feedback is stored with submitted_at timestamp."""
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

        factory = async_sessionmaker(test_engine, class_=AsyncSession)
        async with factory() as session:
            await session.execute(text(
                "INSERT INTO sessions (id, created_at, barriers, expires_at) "
                "VALUES ('sess-fb-4', '2026-03-06', '[]', '2026-04-06')"
            ))
            await session.commit()

        await client.post("/api/feedback/resource", json={
            "resource_id": 3,
            "session_id": "sess-fb-4",
            "helpful": True,
            "barrier_type": "transportation",
        })

        async with factory() as session:
            result = await session.execute(text(
                "SELECT submitted_at, barrier_type FROM resource_feedback "
                "WHERE resource_id = 3 AND session_id = 'sess-fb-4'"
            ))
            row = result.fetchone()
            assert row is not None
            assert row[0] is not None  # submitted_at set
            assert row[1] == "transportation"

    @pytest.mark.anyio
    async def test_invalid_body_returns_422(self, client):
        """Missing required fields returns 422."""
        resp = await client.post("/api/feedback/resource", json={
            "resource_id": 1,
            # missing session_id and helpful
        })
        assert resp.status_code == 422


async def _seed_session_and_token(test_engine, session_id: str, *, expired: bool = False):
    """Helper: insert a session + feedback token. Returns the token string."""
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    factory = async_sessionmaker(test_engine, class_=AsyncSession)
    async with factory() as session:
        await session.execute(text(
            "INSERT INTO sessions (id, created_at, barriers, expires_at) "
            "VALUES (:sid, '2026-03-06', '[]', '2026-04-06')"
        ), {"sid": session_id})

        expires = "2020-01-01T00:00:00" if expired else "2099-01-01T00:00:00"
        token = f"tok-{session_id}"
        await session.execute(text(
            "INSERT INTO feedback_tokens (token, session_id, created_at, expires_at) "
            "VALUES (:token, :sid, '2026-03-06T00:00:00', :expires)"
        ), {"token": token, "sid": session_id, "expires": expires})
        await session.commit()
    return token


class TestValidateTokenEndpoint:
    """GET /api/feedback/validate/{token} — token validation."""

    @pytest.mark.anyio
    async def test_valid_token_returns_200(self, client, test_engine):
        token = await _seed_session_and_token(test_engine, "sess-val-1")
        resp = await client.get(f"/api/feedback/validate/{token}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is True
        assert data["session_id"] == "sess-val-1"

    @pytest.mark.anyio
    async def test_expired_token_returns_410(self, client, test_engine):
        token = await _seed_session_and_token(test_engine, "sess-val-2", expired=True)
        resp = await client.get(f"/api/feedback/validate/{token}")
        assert resp.status_code == 410

    @pytest.mark.anyio
    async def test_unknown_token_returns_404(self, client):
        resp = await client.get("/api/feedback/validate/totally-unknown-token")
        assert resp.status_code == 404


class TestVisitFeedbackEndpoint:
    """POST /api/feedback/visit — visit feedback submission."""

    @pytest.mark.anyio
    async def test_valid_submission_returns_200(self, client, test_engine):
        token = await _seed_session_and_token(test_engine, "sess-visit-1")
        resp = await client.post("/api/feedback/visit", json={
            "token": token,
            "made_it_to_center": 2,
            "outcomes": ["got_interview", "resume_help"],
            "plan_accuracy": 3,
            "free_text": "Very helpful!",
        })
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    @pytest.mark.anyio
    async def test_outcomes_stored_as_json(self, client, test_engine):
        """Outcomes list is persisted as a JSON array in the DB."""
        import json
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

        token = await _seed_session_and_token(test_engine, "sess-visit-2")
        await client.post("/api/feedback/visit", json={
            "token": token,
            "made_it_to_center": 1,
            "outcomes": ["resume_help"],
            "plan_accuracy": 2,
        })

        factory = async_sessionmaker(test_engine, class_=AsyncSession)
        async with factory() as session:
            result = await session.execute(text(
                "SELECT outcomes FROM visit_feedback WHERE session_id = 'sess-visit-2'"
            ))
            row = result.fetchone()
            assert row is not None
            assert json.loads(row[0]) == ["resume_help"]

    @pytest.mark.anyio
    async def test_expired_token_returns_410(self, client, test_engine):
        token = await _seed_session_and_token(test_engine, "sess-visit-3", expired=True)
        resp = await client.post("/api/feedback/visit", json={
            "token": token,
            "made_it_to_center": 0,
            "outcomes": [],
            "plan_accuracy": 1,
        })
        assert resp.status_code == 410

    @pytest.mark.anyio
    async def test_unknown_token_returns_404(self, client):
        resp = await client.post("/api/feedback/visit", json={
            "token": "no-such-token",
            "made_it_to_center": 0,
            "outcomes": [],
            "plan_accuracy": 1,
        })
        assert resp.status_code == 404

    @pytest.mark.anyio
    async def test_duplicate_submission_returns_409(self, client, test_engine):
        token = await _seed_session_and_token(test_engine, "sess-visit-4")
        payload = {
            "token": token,
            "made_it_to_center": 2,
            "outcomes": [],
            "plan_accuracy": 2,
        }
        resp1 = await client.post("/api/feedback/visit", json=payload)
        assert resp1.status_code == 200

        resp2 = await client.post("/api/feedback/visit", json=payload)
        assert resp2.status_code == 409

    @pytest.mark.anyio
    async def test_invalid_body_returns_422(self, client):
        resp = await client.post("/api/feedback/visit", json={
            "token": "x",
            # made_it_to_center out of range
            "made_it_to_center": 5,
            "plan_accuracy": 1,
        })
        assert resp.status_code == 422

"""Tests for feedback routes — resource feedback endpoint."""

import pytest
from fastapi import HTTPException

from app.routes.feedback import _rate_limiter


@pytest.fixture(autouse=True)
def _clear_feedback_rate_limiter():
    _rate_limiter.clear()
    yield
    _rate_limiter.clear()


class TestResourceFeedbackEndpoint:
    """POST /api/feedback/resource — one-tap resource feedback."""

    @pytest.mark.anyio
    async def test_valid_feedback_returns_200(self, client, test_engine):
        """Valid feedback submission returns success."""
        token = await _seed_session_and_token(test_engine, "00000000-0000-4000-8000-f00dbac00001")

        resp = await client.post("/api/feedback/resource", json={
            "resource_id": 1,
            "session_id": "00000000-0000-4000-8000-f00dbac00001",
            "helpful": True,
            "barrier_type": "credit",
            "token": token,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["resource_id"] == 1
        assert data["helpful"] is True

    @pytest.mark.anyio
    async def test_feedback_without_barrier_type(self, client, test_engine):
        """Feedback without optional barrier_type is accepted."""
        token = await _seed_session_and_token(test_engine, "00000000-0000-4000-8000-f00dbac00002")

        resp = await client.post("/api/feedback/resource", json={
            "resource_id": 2,
            "session_id": "00000000-0000-4000-8000-f00dbac00002",
            "helpful": False,
            "token": token,
        })
        assert resp.status_code == 200
        assert resp.json()["helpful"] is False

    @pytest.mark.anyio
    async def test_unknown_session_returns_401(self, client):
        """Feedback with unknown token returns 401."""
        resp = await client.post("/api/feedback/resource", json={
            "resource_id": 1,
            "session_id": "00000000-0000-4000-8000-ffffffffffff",
            "helpful": True,
            "token": "nonexistent-token",
        })
        assert resp.status_code == 401

    @pytest.mark.anyio
    async def test_upsert_updates_existing_vote(self, client, test_engine):
        """Re-voting on same resource+session updates instead of duplicating."""
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

        token = await _seed_session_and_token(test_engine, "00000000-0000-4000-8000-f00dbac00003")

        # First vote: helpful
        resp1 = await client.post("/api/feedback/resource", json={
            "resource_id": 5,
            "session_id": "00000000-0000-4000-8000-f00dbac00003",
            "helpful": True,
            "token": token,
        })
        assert resp1.status_code == 200

        # Second vote: not helpful (should update, not duplicate)
        resp2 = await client.post("/api/feedback/resource", json={
            "resource_id": 5,
            "session_id": "00000000-0000-4000-8000-f00dbac00003",
            "helpful": False,
            "token": token,
        })
        assert resp2.status_code == 200
        assert resp2.json()["helpful"] is False

        # Verify only one row exists
        factory = async_sessionmaker(test_engine, class_=AsyncSession)
        async with factory() as session:
            result = await session.execute(text(
                "SELECT COUNT(*) FROM resource_feedback "
                "WHERE resource_id = 5 AND session_id = '00000000-0000-4000-8000-f00dbac00003'"
            ))
            count = result.scalar()
            assert count == 1

            # Verify it's the updated value
            result = await session.execute(text(
                "SELECT helpful FROM resource_feedback "
                "WHERE resource_id = 5 AND session_id = '00000000-0000-4000-8000-f00dbac00003'"
            ))
            assert result.scalar() == 0  # False = 0

    @pytest.mark.anyio
    async def test_feedback_persisted_with_timestamp(self, client, test_engine):
        """Feedback is stored with submitted_at timestamp."""
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

        token = await _seed_session_and_token(test_engine, "00000000-0000-4000-8000-f00dbac00004")

        await client.post("/api/feedback/resource", json={
            "resource_id": 3,
            "session_id": "00000000-0000-4000-8000-f00dbac00004",
            "helpful": True,
            "barrier_type": "transportation",
            "token": token,
        })

        factory = async_sessionmaker(test_engine, class_=AsyncSession)
        async with factory() as session:
            result = await session.execute(text(
                "SELECT submitted_at, barrier_type FROM resource_feedback "
                "WHERE resource_id = 3 AND session_id = '00000000-0000-4000-8000-f00dbac00004'"
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
            # missing session_id, helpful, and token
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


# --- SEC-023: Info leak prevention ---

class TestValidateEndpointInfoLeak:
    """Validate endpoint should NOT return session_id."""

    @pytest.mark.anyio
    async def test_valid_token_does_not_leak_session_id(self, client, test_engine):
        token = await _seed_session_and_token(test_engine, "sess-noleak")
        resp = await client.get(f"/api/feedback/validate/{token}")
        assert resp.status_code == 200
        data = resp.json()
        assert "session_id" not in data


# --- SEC-012: Body field validation ---

class TestResourceFeedbackSessionIdValidation:
    """ResourceFeedbackRequest.session_id rejects non-UUID format."""

    @pytest.mark.anyio
    async def test_non_uuid_session_id_returns_422(self, client):
        resp = await client.post("/api/feedback/resource", json={
            "resource_id": 1,
            "session_id": "not-a-uuid",
            "helpful": True,
            "token": "some-token",
        })
        assert resp.status_code == 422


# --- SEC-005: Resource feedback requires token ---

class TestResourceFeedbackTokenAuth:
    """POST /api/feedback/resource requires a valid token matching session_id."""

    @pytest.mark.anyio
    async def test_missing_token_returns_422(self, client, test_engine):
        """Request without token field returns 422."""
        resp = await client.post("/api/feedback/resource", json={
            "resource_id": 1,
            "session_id": "00000000-0000-4000-8000-f00dbac00001",
            "helpful": True,
        })
        assert resp.status_code == 422

    @pytest.mark.anyio
    async def test_invalid_token_returns_401(self, client, test_engine):
        """Request with invalid token returns 401."""
        await _seed_session_and_token(test_engine, "00000000-0000-4000-8000-f00dbac00010")
        resp = await client.post("/api/feedback/resource", json={
            "resource_id": 1,
            "session_id": "00000000-0000-4000-8000-f00dbac00010",
            "helpful": True,
            "token": "bad-token",
        })
        assert resp.status_code == 401

    @pytest.mark.anyio
    async def test_mismatched_token_returns_403(self, client, test_engine):
        """Token for different session returns 403."""
        await _seed_session_and_token(test_engine, "00000000-0000-4000-8000-f00dbac00011")
        token = await _seed_session_and_token(test_engine, "00000000-0000-4000-8000-f00dbac00012")
        resp = await client.post("/api/feedback/resource", json={
            "resource_id": 1,
            "session_id": "00000000-0000-4000-8000-f00dbac00011",
            "helpful": True,
            "token": token,  # token belongs to f00dbac00012, not f00dbac00011
        })
        assert resp.status_code == 403

    @pytest.mark.anyio
    async def test_valid_token_succeeds(self, client, test_engine):
        """Valid matching token allows feedback submission."""
        token = await _seed_session_and_token(test_engine, "00000000-0000-4000-8000-f00dbac00013")
        resp = await client.post("/api/feedback/resource", json={
            "resource_id": 1,
            "session_id": "00000000-0000-4000-8000-f00dbac00013",
            "helpful": True,
            "token": token,
        })
        assert resp.status_code == 200
        assert resp.json()["success"] is True


# --- Direct handler tests for coverage ---

from unittest.mock import AsyncMock, MagicMock, patch

from app.routes.feedback import (
    _require_valid_token,
    submit_resource_feedback,
    submit_visit_feedback,
    validate_feedback_token,
)
from app.modules.feedback.types import (
    ResourceFeedbackRequest,
    ResourceFeedbackResponse,
    VisitFeedbackRequest,
    VisitFeedbackResponse,
)


class TestFeedbackHandlersDirect:
    """Direct handler calls (no ASGI) for coverage of route body lines."""

    @pytest.mark.anyio
    async def test_require_valid_token_returns_session_id(self):
        """Valid token returns the associated session_id."""
        mock_db = AsyncMock()
        with patch("app.routes.feedback.validate_token", new_callable=AsyncMock, return_value="sess-1"):
            result = await _require_valid_token(mock_db, "good-token")
        assert result == "sess-1"

    @pytest.mark.anyio
    async def test_require_valid_token_expired_raises_410(self):
        """Expired token raises HTTPException 410."""
        mock_db = AsyncMock()
        with (
            patch("app.routes.feedback.validate_token", new_callable=AsyncMock, return_value=None),
            patch("app.routes.feedback.token_exists", new_callable=AsyncMock, return_value=True),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await _require_valid_token(mock_db, "expired-token")
        assert exc_info.value.status_code == 410

    @pytest.mark.anyio
    async def test_require_valid_token_unknown_raises_404(self):
        """Unknown token raises HTTPException 404."""
        mock_db = AsyncMock()
        with (
            patch("app.routes.feedback.validate_token", new_callable=AsyncMock, return_value=None),
            patch("app.routes.feedback.token_exists", new_callable=AsyncMock, return_value=False),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await _require_valid_token(mock_db, "unknown-token")
        assert exc_info.value.status_code == 404

    @pytest.mark.anyio
    async def test_submit_resource_feedback_direct(self):
        """Direct call returns ResourceFeedbackResponse with success."""
        mock_db = AsyncMock()
        mock_request = MagicMock()
        mock_request.client.host = "127.0.0.1"

        feedback = ResourceFeedbackRequest(
            resource_id=1,
            session_id="00000000-0000-4000-8000-f00dbac00001",
            helpful=True,
            token="tok-1",
        )
        with (
            patch("app.routes.feedback.require_session_token", new_callable=AsyncMock),
            patch("app.routes.feedback.insert_resource_feedback", new_callable=AsyncMock),
            patch("app.routes.feedback.audit_log"),
        ):
            result = await submit_resource_feedback(feedback, mock_request, mock_db)

        assert isinstance(result, ResourceFeedbackResponse)
        assert result.success is True
        assert result.resource_id == 1
        assert result.helpful is True

    @pytest.mark.anyio
    async def test_validate_feedback_token_direct(self):
        """Direct call returns {valid: True} when token is valid."""
        mock_db = AsyncMock()
        with patch("app.routes.feedback._require_valid_token", new_callable=AsyncMock, return_value="sess-1"):
            result = await validate_feedback_token("test-token", mock_db)
        assert result == {"valid": True}

    @pytest.mark.anyio
    async def test_submit_visit_feedback_direct(self):
        """Direct call returns VisitFeedbackResponse with success."""
        mock_db = AsyncMock()
        mock_request = MagicMock()
        mock_request.client.host = "127.0.0.1"

        feedback = VisitFeedbackRequest(
            token="tok-v1",
            made_it_to_center=2,
            outcomes=["got_interview"],
            plan_accuracy=3,
            free_text="Great!",
        )
        with (
            patch("app.routes.feedback._require_valid_token", new_callable=AsyncMock, return_value="sess-v1"),
            patch("app.routes.feedback.has_visit_feedback", new_callable=AsyncMock, return_value=False),
            patch("app.routes.feedback.insert_visit_feedback", new_callable=AsyncMock),
            patch("app.routes.feedback.audit_log"),
        ):
            result = await submit_visit_feedback(feedback, mock_request, mock_db)

        assert isinstance(result, VisitFeedbackResponse)
        assert result.success is True

    @pytest.mark.anyio
    async def test_submit_visit_feedback_duplicate_raises_409(self):
        """When has_visit_feedback is True, submit_visit_feedback raises 409."""
        mock_db = AsyncMock()
        mock_request = MagicMock()
        mock_request.client.host = "127.0.0.1"

        feedback = VisitFeedbackRequest(
            token="tok-1",
            made_it_to_center=2,
            outcomes=[],
            plan_accuracy=3,
        )
        with (
            patch("app.routes.feedback._require_valid_token", new_callable=AsyncMock, return_value="sess-1"),
            patch("app.routes.feedback.has_visit_feedback", new_callable=AsyncMock, return_value=True),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await submit_visit_feedback(feedback, mock_request, mock_db)
            assert exc_info.value.status_code == 409

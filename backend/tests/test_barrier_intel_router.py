"""Tests for barrier intelligence chat endpoint."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.responses import StreamingResponse

from app.barrier_intel.cache import RETRIEVAL_CACHE
from app.barrier_intel.guardrails import is_disallowed_topic
from app.barrier_intel.prompts import SYSTEM_PROMPT, build_user_prompt
from app.barrier_intel.router import _get_retrieval_ctx, _rate_limiter, chat, reindex
from app.barrier_intel.schemas import ChatRequest
from app.core.database import get_async_session_factory
from app.core.queries import create_session
from app.main import app
from app.rag.document_schema import RetrievalContext
from app.rag.store import RagStore


_RETRIEVE_PATCH = "app.barrier_intel.router.retrieve_context"
_STREAM_PATCH = "app.barrier_intel.router.anthropic.AsyncAnthropic"


def _mock_session_row(barriers="[\"CREDIT_LOW_SCORE\"]"):
    return {
        "id": "test-session-id",
        "barriers": barriers,
        "credit_profile": None,
        "qualifications": None,
        "plan": None,
        "profile": json.dumps({"zip_code": "36104"}),
        "created_at": "2026-03-08T00:00:00",
        "expires_at": "2099-03-09T00:00:00",
    }


def _mock_retrieval_context():
    return RetrievalContext(
        root_barriers=[{"id": "CREDIT_LOW_SCORE", "name": "Low Credit Score", "category": "credit"}],
        barrier_chain_summary="Low Credit Score",
        top_resources=[{"name": "GreenPath Financial", "resource_id": 14, "impact_strength": 0.85}],
        retrieved_docs=[{"id": "resource_14", "title": "GreenPath", "text": "Credit counseling"}],
        retrieval_latency_ms=12.5,
    )


class TestGuardrails:
    def test_allows_normal_question(self):
        assert is_disallowed_topic("What should I do first?") is False

    def test_blocks_legal_advice(self):
        assert is_disallowed_topic("Can you give me legal advice about my case?") is True

    def test_blocks_medical_advice(self):
        assert is_disallowed_topic("What medication should I take?") is True

    def test_blocks_immigration(self):
        assert is_disallowed_topic("Help me with my immigration status") is True

    def test_case_insensitive(self):
        assert is_disallowed_topic("I need LEGAL ADVICE please") is True


class TestPrompts:
    def test_system_prompt_has_rules(self):
        assert "RULES" in SYSTEM_PROMPT
        assert "6th" in SYSTEM_PROMPT or "eighth" in SYSTEM_PROMPT or "reading level" in SYSTEM_PROMPT

    def test_build_user_prompt_includes_context(self):
        ctx = _mock_retrieval_context()
        prompt = build_user_prompt("What should I do first?", "next_steps", ctx)
        assert "CREDIT_LOW_SCORE" in prompt or "Low Credit Score" in prompt
        assert "GreenPath" in prompt


class TestChatRequestValidation:
    def test_valid_next_steps_mode(self):
        req = ChatRequest(session_id="00000000-0000-0000-0000-000000000001", user_question="What next?", mode="next_steps")
        assert req.mode == "next_steps"

    def test_valid_explain_plan_mode(self):
        req = ChatRequest(session_id="00000000-0000-0000-0000-000000000001", user_question="Why?", mode="explain_plan")
        assert req.mode == "explain_plan"

    def test_invalid_mode_rejected(self):
        with pytest.raises(Exception):
            ChatRequest(session_id="00000000-0000-0000-0000-000000000001", user_question="What if?", mode="what_if")

    def test_invalid_session_id_rejected(self):
        with pytest.raises(Exception):
            ChatRequest(session_id="not-a-uuid", user_question="Hello", mode="next_steps")


class TestReindexEndpoint:
    @pytest.mark.anyio
    async def test_reindex_without_admin_key_returns_422(self, client):
        """POST /reindex without X-Admin-Key header returns 422 (missing header)."""
        resp = await client.post("/api/barrier-intel/reindex")
        assert resp.status_code == 422

    @pytest.mark.anyio
    async def test_reindex_with_wrong_admin_key_returns_403(self, client, test_engine):
        """POST /reindex with wrong admin key returns 403."""
        with patch("app.core.auth.get_settings") as mock_settings:
            s = MagicMock()
            s.admin_api_key = "ok-key"
            mock_settings.return_value = s
            resp = await client.post(
                "/api/barrier-intel/reindex",
                headers={"X-Admin-Key": "bad-key"},
            )
        assert resp.status_code == 403


class TestChatStreaming:
    @pytest.mark.anyio
    async def test_chat_returns_streaming_response(self, client, test_engine):
        """POST /chat with valid session returns SSE stream (200)."""
        # Ensure rag_store is available on app.state
        store = RagStore()
        app.state.rag_store = store

        factory = get_async_session_factory()
        async with factory() as session:
            await create_session(session, {
                "barriers": '["CREDIT_LOW_SCORE"]',
                "profile": '{"zip_code": "36104"}',
            }, session_id="00000000-0000-0000-0000-000000000002")

        with patch("app.barrier_intel.streaming.get_llm_stream") as mock_stream, \
             patch(_TOKEN_PATCH, new_callable=AsyncMock):
            async def fake_stream(*args, **kwargs):
                yield "Hello"
                yield " world"

            mock_stream.return_value = fake_stream()

            resp = await client.post(
                "/api/barrier-intel/chat?token=test",
                json={"session_id": "00000000-0000-0000-0000-000000000002", "user_question": "What should I do first?", "mode": "next_steps"},
            )
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers.get("content-type", "")


class TestGetRetrievalCtxCache:
    @pytest.mark.anyio
    async def test_get_retrieval_ctx_uses_cache(self):
        """Second call with same cache_key should return cached result."""
        RETRIEVAL_CACHE.clear()

        fake_ctx = {"root_barriers": ["X"], "docs": []}
        cache_key = "test-cache-key-123"

        # Pre-populate cache
        RETRIEVAL_CACHE[cache_key] = fake_ctx

        # Call with a cache_key that already exists; should NOT call retrieve_context
        result = await _get_retrieval_ctx(
            cache_key, ["CREDIT_LOW_SCORE"], None, None, {}
        )
        assert result == fake_ctx
        RETRIEVAL_CACHE.clear()

    @pytest.mark.anyio
    async def test_get_retrieval_ctx_cache_miss(self):
        """Cache miss calls retrieve_context and caches the result."""
        RETRIEVAL_CACHE.clear()
        fake_ctx = _mock_retrieval_context()

        with patch(
            "app.barrier_intel.router.retrieve_context",
            new_callable=AsyncMock,
            return_value=fake_ctx,
        ) as mock_retrieve:
            result = await _get_retrieval_ctx(
                "miss-key", ["CREDIT_LOW_SCORE"], MagicMock(), MagicMock(),
                {"zip_code": "36104"},
            )

        mock_retrieve.assert_called_once()
        assert result == fake_ctx
        assert RETRIEVAL_CACHE.get("miss-key") == fake_ctx
        RETRIEVAL_CACHE.clear()


class TestReindexDirect:
    """Direct unit tests for the reindex endpoint function."""

    @pytest.mark.anyio
    async def test_reindex_success(self):
        """Calling reindex rebuilds the store and returns document count."""
        mock_store = MagicMock()
        mock_store.rebuild = AsyncMock(return_value=42)
        mock_request = MagicMock()
        mock_request.app.state.rag_store = mock_store
        mock_db = AsyncMock()

        result = await reindex(request=mock_request, db=mock_db)

        mock_store.rebuild.assert_awaited_once_with(mock_db)
        assert result == {"status": "ok", "documents_indexed": 42}


_TOKEN_PATCH = "app.barrier_intel.router.require_session_token"


class TestChatDirect:
    """Direct unit tests for the chat endpoint function (bypasses ASGI)."""

    @pytest.mark.anyio
    async def test_missing_session_raises_404(self):
        body = ChatRequest(
            session_id="00000000-0000-0000-0000-000000000099", user_question="Hi", mode="next_steps",
        )
        mock_request = MagicMock()
        mock_db = AsyncMock()

        with patch(
            "app.barrier_intel.router.get_session_by_id",
            new_callable=AsyncMock,
            return_value=None,
        ), patch(_TOKEN_PATCH, new_callable=AsyncMock):
            with pytest.raises(HTTPException) as exc_info:
                await chat(body=body, request=mock_request, db=mock_db, token="t")
            assert exc_info.value.status_code == 404

    @pytest.mark.anyio
    async def test_disallowed_topic_returns_safe_message(self):
        body = ChatRequest(
            session_id="00000000-0000-0000-0000-000000000001", user_question="Give me legal advice", mode="next_steps",
        )
        mock_request = MagicMock()
        mock_db = AsyncMock()

        with patch(
            "app.barrier_intel.router.get_session_by_id",
            new_callable=AsyncMock,
            return_value=_mock_session_row(),
        ), patch(_TOKEN_PATCH, new_callable=AsyncMock):
            result = await chat(body=body, request=mock_request, db=mock_db, token="t")

        assert result["guardrail_triggered"] is True
        assert "not able" in result["message"].lower()

    @pytest.mark.anyio
    async def test_valid_question_returns_streaming_response(self):
        body = ChatRequest(
            session_id="00000000-0000-0000-0000-000000000001", user_question="What should I do first?",
            mode="next_steps",
        )
        mock_request = MagicMock()
        mock_request.app.state.rag_store = MagicMock()
        mock_db = AsyncMock()

        with patch(
            "app.barrier_intel.router.get_session_by_id",
            new_callable=AsyncMock,
            return_value=_mock_session_row(),
        ), patch(
            "app.barrier_intel.router._get_retrieval_ctx",
            new_callable=AsyncMock,
            return_value=_mock_retrieval_context(),
        ), patch(_TOKEN_PATCH, new_callable=AsyncMock):
            result = await chat(body=body, request=mock_request, db=mock_db, token="t")

        assert isinstance(result, StreamingResponse)
        assert result.media_type == "text/event-stream"


class TestChatAuth:
    """Tests for session token authentication on chat endpoint (B-H2)."""

    @pytest.mark.anyio
    async def test_missing_token_returns_401(self):
        body = ChatRequest(
            session_id="00000000-0000-0000-0000-000000000001",
            user_question="What should I do?",
            mode="next_steps",
        )
        mock_request = MagicMock()
        mock_db = AsyncMock()

        with patch(
            "app.barrier_intel.router.get_session_by_id",
            new_callable=AsyncMock,
            return_value=_mock_session_row(),
        ), patch(
            "app.barrier_intel.router.require_session_token",
            new_callable=AsyncMock,
            side_effect=HTTPException(status_code=401, detail="Invalid token"),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await chat(body=body, request=mock_request, db=mock_db, token="bad-token")
            assert exc_info.value.status_code == 401

    @pytest.mark.anyio
    async def test_valid_token_proceeds(self):
        body = ChatRequest(
            session_id="00000000-0000-0000-0000-000000000001",
            user_question="What should I do first?",
            mode="next_steps",
        )
        mock_request = MagicMock()
        mock_request.app.state.rag_store = MagicMock()
        mock_db = AsyncMock()

        with patch(
            "app.barrier_intel.router.get_session_by_id",
            new_callable=AsyncMock,
            return_value=_mock_session_row(),
        ), patch(
            "app.barrier_intel.router.require_session_token",
            new_callable=AsyncMock,
        ), patch(
            "app.barrier_intel.router._get_retrieval_ctx",
            new_callable=AsyncMock,
            return_value=_mock_retrieval_context(),
        ):
            result = await chat(body=body, request=mock_request, db=mock_db, token="valid-token")

        assert isinstance(result, StreamingResponse)


class TestChatCorruptSession:
    """Tests for corrupt session data handling (B-H3)."""

    @pytest.mark.anyio
    async def test_corrupt_barriers_json_returns_400(self):
        body = ChatRequest(
            session_id="00000000-0000-0000-0000-000000000001",
            user_question="What should I do?",
            mode="next_steps",
        )
        mock_request = MagicMock()
        mock_request.app.state.rag_store = MagicMock()
        mock_db = AsyncMock()

        with patch(
            "app.barrier_intel.router.get_session_by_id",
            new_callable=AsyncMock,
            return_value=_mock_session_row(barriers="{corrupt json!!!"),
        ), patch(_TOKEN_PATCH, new_callable=AsyncMock):
            with pytest.raises(HTTPException) as exc_info:
                await chat(body=body, request=mock_request, db=mock_db, token="t")
            assert exc_info.value.status_code == 400
            assert "corrupt" in exc_info.value.detail.lower()

    @pytest.mark.anyio
    async def test_corrupt_profile_json_returns_400(self):
        body = ChatRequest(
            session_id="00000000-0000-0000-0000-000000000001",
            user_question="What should I do?",
            mode="next_steps",
        )
        row = _mock_session_row()
        row["profile"] = "{not valid json"
        mock_request = MagicMock()
        mock_request.app.state.rag_store = MagicMock()
        mock_db = AsyncMock()

        with patch(
            "app.barrier_intel.router.get_session_by_id",
            new_callable=AsyncMock,
            return_value=row,
        ), patch(_TOKEN_PATCH, new_callable=AsyncMock):
            with pytest.raises(HTTPException) as exc_info:
                await chat(body=body, request=mock_request, db=mock_db, token="t")
            assert exc_info.value.status_code == 400
            assert "corrupt" in exc_info.value.detail.lower()


class TestChatEndpoint:
    @pytest.mark.anyio
    async def test_missing_token_returns_422(self, client):
        """POST /chat without token query param returns 422."""
        resp = await client.post(
            "/api/barrier-intel/chat",
            json={"session_id": "00000000-0000-0000-0000-999999999999", "user_question": "Hello", "mode": "next_steps"},
        )
        assert resp.status_code == 422

    @pytest.mark.anyio
    async def test_missing_session_returns_404(self, client):
        with patch(_TOKEN_PATCH, new_callable=AsyncMock):
            resp = await client.post(
                "/api/barrier-intel/chat?token=test",
                json={"session_id": "00000000-0000-0000-0000-999999999999", "user_question": "Hello", "mode": "next_steps"},
            )
        assert resp.status_code == 404

    @pytest.mark.anyio
    async def test_disallowed_topic_returns_safe_response(self, client, test_engine):
        factory = get_async_session_factory()
        async with factory() as session:
            await create_session(session, {
                "barriers": '["CREDIT_LOW_SCORE"]',
                "profile": '{"zip_code": "36104"}',
            }, session_id="00000000-0000-0000-0000-000000000002")

        with patch(_TOKEN_PATCH, new_callable=AsyncMock):
            resp = await client.post(
                "/api/barrier-intel/chat?token=test",
                json={"session_id": "00000000-0000-0000-0000-000000000002", "user_question": "Give me legal advice", "mode": "next_steps"},
            )
        assert resp.status_code == 200
        body = resp.json()
        assert "not able" in body["message"].lower() or "counselor" in body["message"].lower()

    @pytest.mark.anyio
    async def test_rate_limiting(self, client, test_engine):
        _rate_limiter.clear()
        for _ in range(11):
            resp = await client.post(
                "/api/barrier-intel/chat?token=test",
                json={"session_id": "x", "user_question": "Hello", "mode": "next_steps"},
            )
        assert resp.status_code == 429

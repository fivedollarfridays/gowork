"""Tests for barrier intelligence chat endpoint."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.barrier_intel.guardrails import is_disallowed_topic
from app.barrier_intel.prompts import SYSTEM_PROMPT, build_user_prompt
from app.barrier_intel.schemas import ChatRequest
from app.rag.document_schema import RetrievalContext


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


class TestChatEndpoint:
    @pytest.mark.anyio
    async def test_missing_session_returns_404(self, client):
        resp = await client.post(
            "/api/barrier-intel/chat",
            json={"session_id": "00000000-0000-0000-0000-999999999999", "user_question": "Hello", "mode": "next_steps"},
        )
        assert resp.status_code == 404

    @pytest.mark.anyio
    async def test_disallowed_topic_returns_safe_response(self, client, test_engine):
        from app.core.database import get_async_session_factory
        from app.core.queries import create_session

        factory = get_async_session_factory()
        async with factory() as session:
            await create_session(session, {
                "barriers": '["CREDIT_LOW_SCORE"]',
                "profile": '{"zip_code": "36104"}',
            }, session_id="00000000-0000-0000-0000-000000000002")

        resp = await client.post(
            "/api/barrier-intel/chat",
            json={"session_id": "00000000-0000-0000-0000-000000000002", "user_question": "Give me legal advice", "mode": "next_steps"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "not able" in body["message"].lower() or "counselor" in body["message"].lower()

    @pytest.mark.anyio
    async def test_rate_limiting(self, client, test_engine):
        from app.barrier_intel.router import _rate_limiter
        _rate_limiter.clear()
        for _ in range(11):
            resp = await client.post(
                "/api/barrier-intel/chat",
                json={"session_id": "x", "user_question": "Hello", "mode": "next_steps"},
            )
        assert resp.status_code == 429

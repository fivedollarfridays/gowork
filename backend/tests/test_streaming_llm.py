"""Tests for streaming.py wired to multi-provider LLM client."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.barrier_intel.streaming import format_sse, stream_chat_response
from app.rag.document_schema import RetrievalContext


def _mock_ctx():
    return RetrievalContext(
        root_barriers=[{"id": "CREDIT_LOW_SCORE", "name": "Low Credit Score", "category": "credit"}],
        barrier_chain_summary="Low Credit Score",
        top_resources=[{"name": "GreenPath", "resource_id": 14, "impact_strength": 0.85}],
        retrieved_docs=[{"id": "resource_14", "title": "GreenPath", "text": "Credit counseling"}],
        retrieval_latency_ms=12.5,
    )


class TestFormatSse:
    def test_dict_data(self):
        result = format_sse("context", {"key": "value"})
        assert result.startswith("data: ")
        assert result.endswith("\n\n")
        parsed = json.loads(result[6:].strip())
        assert parsed["type"] == "context"
        assert parsed["key"] == "value"

    def test_string_data(self):
        result = format_sse("token", "hello")
        parsed = json.loads(result[6:].strip())
        assert parsed["type"] == "token"
        assert parsed["text"] == "hello"


@pytest.mark.anyio
class TestStreamChatResponseWithLlmClient:
    """Test that stream_chat_response uses get_llm_stream instead of Anthropic SDK."""

    async def test_yields_context_then_tokens_then_done(self):
        """SSE protocol: context → token* → done."""
        async def fake_llm_stream(system_prompt, user_prompt):
            yield "Hello "
            yield "world"

        ctx = _mock_ctx()
        with patch("app.barrier_intel.streaming.get_llm_stream", return_value=fake_llm_stream("s", "u")):
            events = []
            async for event in stream_chat_response(
                question="What should I do?",
                mode="next_steps",
                ctx=ctx,
                session_hash="abc123",
            ):
                events.append(event)

        assert len(events) == 4  # context + 2 tokens + done
        # First event is context
        ctx_data = json.loads(events[0][6:].strip())
        assert ctx_data["type"] == "context"
        assert "CREDIT_LOW_SCORE" in ctx_data["root_barriers"]

        # Middle events are tokens
        tok1 = json.loads(events[1][6:].strip())
        assert tok1["type"] == "token"
        assert tok1["text"] == "Hello "

        tok2 = json.loads(events[2][6:].strip())
        assert tok2["type"] == "token"
        assert tok2["text"] == "world"

        # Last event is done
        done_data = json.loads(events[3][6:].strip())
        assert done_data["type"] == "done"
        assert "latency_ms" in done_data

    async def test_no_api_key_and_model_params(self):
        """stream_chat_response should NOT require api_key/model params anymore."""
        async def fake_llm_stream(system_prompt, user_prompt):
            yield "chunk"

        ctx = _mock_ctx()
        with patch("app.barrier_intel.streaming.get_llm_stream", return_value=fake_llm_stream("s", "u")):
            events = []
            # Should work without api_key and model
            async for event in stream_chat_response(
                question="Hello",
                mode="next_steps",
                ctx=ctx,
                session_hash="hash123",
            ):
                events.append(event)
        assert len(events) == 3  # context + 1 token + done

    async def test_passes_system_prompt_and_user_prompt(self):
        """Verify correct prompts are passed to get_llm_stream."""
        captured_args = {}

        async def capturing_stream(system_prompt, user_prompt):
            captured_args["system"] = system_prompt
            captured_args["user"] = user_prompt
            yield "response"

        ctx = _mock_ctx()
        with patch("app.barrier_intel.streaming.get_llm_stream", side_effect=capturing_stream):
            events = []
            async for event in stream_chat_response(
                question="What should I do?",
                mode="next_steps",
                ctx=ctx,
                session_hash="hash",
            ):
                events.append(event)

        assert "system" in captured_args
        assert "RULES" in captured_args["system"] or "navigator" in captured_args["system"].lower()
        assert "user" in captured_args


@pytest.mark.anyio
class TestGenerateNarrativeWithLlmClient:
    """Test that generate_narrative uses get_llm_stream."""

    async def test_collects_streamed_json(self):
        from app.ai.client import generate_narrative

        response_json = json.dumps({
            "summary": "Visit the career center Monday.",
            "key_actions": ["Call GreenPath", "Check transit routes"],
        })

        async def fake_stream(system_prompt, user_prompt):
            # Simulate streaming JSON in chunks
            for i in range(0, len(response_json), 20):
                yield response_json[i:i + 20]

        with patch("app.ai.client.get_llm_stream", return_value=fake_stream("s", "u")):
            result = await generate_narrative(
                barriers=["credit"],
                qualifications="Former CNA",
                plan_data={"barriers": [], "job_matches": []},
            )
        assert result.summary == "Visit the career center Monday."
        assert len(result.key_actions) == 2

    async def test_invalid_json_raises(self):
        from app.ai.client import generate_narrative

        async def bad_stream(system_prompt, user_prompt):
            yield "not valid json at all"

        with patch("app.ai.client.get_llm_stream", return_value=bad_stream("s", "u")):
            with pytest.raises(ValueError, match="invalid JSON"):
                await generate_narrative(
                    barriers=["credit"],
                    qualifications="",
                    plan_data={},
                )

    async def test_empty_response_raises(self):
        from app.ai.client import generate_narrative

        async def empty_stream(system_prompt, user_prompt):
            return
            yield  # noqa: unreachable - makes this an async generator

        with patch("app.ai.client.get_llm_stream", return_value=empty_stream("s", "u")):
            with pytest.raises(ValueError, match="empty"):
                await generate_narrative(
                    barriers=["credit"],
                    qualifications="",
                    plan_data={},
                )


@pytest.mark.anyio
class TestHallucinationGuardIntegration:
    """Test hallucination guard wired into stream_chat_response."""

    async def test_emits_disclaimer_for_hallucinated_resource(self):
        """When response mentions unknown resource, disclaimer event emitted."""
        async def fake_stream(system_prompt, user_prompt):
            yield "Visit the Springfield Job Center for help."

        ctx = _mock_ctx()  # top_resources has "GreenPath" only
        with patch("app.barrier_intel.streaming.get_llm_stream", return_value=fake_stream("s", "u")):
            events = []
            async for event in stream_chat_response(
                question="What should I do?",
                mode="next_steps",
                ctx=ctx,
                session_hash="abc",
            ):
                events.append(event)

        # Expect: context + token + disclaimer + done
        event_types = [json.loads(e[6:].strip())["type"] for e in events]
        assert "disclaimer" in event_types
        disclaimer = json.loads(events[event_types.index("disclaimer")][6:].strip())
        assert "Springfield Job Center" in disclaimer["text"]

    async def test_no_disclaimer_when_all_resources_known(self):
        """When all mentioned resources are known, no disclaimer emitted."""
        async def fake_stream(system_prompt, user_prompt):
            yield "Contact GreenPath for credit counseling."

        ctx = _mock_ctx()  # top_resources has "GreenPath"
        with patch("app.barrier_intel.streaming.get_llm_stream", return_value=fake_stream("s", "u")):
            events = []
            async for event in stream_chat_response(
                question="What should I do?",
                mode="next_steps",
                ctx=ctx,
                session_hash="abc",
            ):
                events.append(event)

        event_types = [json.loads(e[6:].strip())["type"] for e in events]
        assert "disclaimer" not in event_types

    async def test_no_disclaimer_when_no_org_names_mentioned(self):
        """Plain text response with no proper nouns triggers no disclaimer."""
        async def fake_stream(system_prompt, user_prompt):
            yield "Check your credit report and review the bus schedule."

        ctx = _mock_ctx()
        with patch("app.barrier_intel.streaming.get_llm_stream", return_value=fake_stream("s", "u")):
            events = []
            async for event in stream_chat_response(
                question="What should I do?",
                mode="next_steps",
                ctx=ctx,
                session_hash="abc",
            ):
                events.append(event)

        event_types = [json.loads(e[6:].strip())["type"] for e in events]
        assert "disclaimer" not in event_types

    async def test_audit_log_reflects_guardrail_triggered(self):
        """Audit log should indicate guardrail_triggered=True on hallucination."""
        async def fake_stream(system_prompt, user_prompt):
            yield "Visit the Springfield Job Center for help."

        ctx = _mock_ctx()
        with patch("app.barrier_intel.streaming.get_llm_stream", return_value=fake_stream("s", "u")), \
             patch("app.barrier_intel.streaming._audit_log") as mock_audit:
            events = []
            async for event in stream_chat_response(
                question="What should I do?",
                mode="next_steps",
                ctx=ctx,
                session_hash="abc",
            ):
                events.append(event)

        mock_audit.assert_called_once()
        call_kwargs = mock_audit.call_args
        # guardrail_triggered should be passed as True
        assert call_kwargs[1]["guardrail_triggered"] is True

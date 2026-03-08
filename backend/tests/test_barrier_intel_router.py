"""Tests for T24.5 — LLM orchestration + guardrails + SSE streaming."""

import pytest

pytestmark = pytest.mark.anyio


# ---------------------------------------------------------------------------
# Cycle 1: ChatRequest schema validation
# ---------------------------------------------------------------------------

def test_chat_request_valid_next_steps():
    from app.barrier_intel.schemas import ChatRequest

    req = ChatRequest(
        session_id="abc123",
        user_question="What should I do first?",
        mode="next_steps",
    )
    assert req.mode == "next_steps"


def test_chat_request_valid_explain_plan():
    from app.barrier_intel.schemas import ChatRequest

    req = ChatRequest(
        session_id="abc123",
        user_question="Why is childcare listed first?",
        mode="explain_plan",
    )
    assert req.mode == "explain_plan"


def test_chat_request_invalid_mode_raises():
    from app.barrier_intel.schemas import ChatRequest

    with pytest.raises(Exception):
        ChatRequest(
            session_id="abc123",
            user_question="What if I had a car?",
            mode="what_if",
        )


# ---------------------------------------------------------------------------
# Cycle 2: guardrails — is_disallowed_topic
# ---------------------------------------------------------------------------

def test_guardrail_blocks_legal_advice():
    from app.barrier_intel.guardrails import is_disallowed_topic

    assert is_disallowed_topic("Can I sue my employer for wrongful termination?")


def test_guardrail_blocks_medical_advice():
    from app.barrier_intel.guardrails import is_disallowed_topic

    assert is_disallowed_topic("What medication should I take for my diagnosis?")


def test_guardrail_blocks_immigration_question():
    from app.barrier_intel.guardrails import is_disallowed_topic

    assert is_disallowed_topic("How do I get a green card or visa status?")


def test_guardrail_allows_employment_question():
    from app.barrier_intel.guardrails import is_disallowed_topic

    assert not is_disallowed_topic("What childcare resources are available near me?")


# ---------------------------------------------------------------------------
# Cycle 3: audit log — PII-safe JSONL write
# ---------------------------------------------------------------------------

def test_audit_log_writes_jsonl(tmp_path):
    import json
    from app.barrier_intel.audit_log import write_audit_entry

    log_file = tmp_path / "audit.jsonl"
    write_audit_entry(
        log_path=log_file,
        session_id="session-abc-123",
        mode="next_steps",
        root_barriers=["CHILDCARE_EVENING"],
        retrieval_doc_ids=["playbook_CHILDCARE_EVENING", "resource_3"],
        input_tokens=500,
        output_tokens=200,
        latency_ms=980.0,
        guardrail_triggered=False,
    )
    lines = log_file.read_text().strip().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert "session_hash" in entry
    assert "session_id" not in entry  # no PII
    assert entry["mode"] == "next_steps"
    assert entry["guardrail_triggered"] is False


def test_audit_log_hashes_session_id(tmp_path):
    from app.barrier_intel.audit_log import write_audit_entry

    log_file = tmp_path / "audit.jsonl"
    write_audit_entry(
        log_path=log_file,
        session_id="my-real-session-id",
        mode="explain_plan",
        root_barriers=[],
        retrieval_doc_ids=[],
        input_tokens=0,
        output_tokens=0,
        latency_ms=0.0,
        guardrail_triggered=True,
    )
    raw = log_file.read_text()
    assert "my-real-session-id" not in raw  # PII scrubbed


# ---------------------------------------------------------------------------
# Cycle 4: Router — 404 on missing session, 422 on invalid mode
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_chat_missing_session_returns_404(client):
    response = await client.post(
        "/api/barrier-intel/chat",
        json={
            "session_id": "nonexistent-session-id",
            "user_question": "What should I do?",
            "mode": "next_steps",
        },
    )
    assert response.status_code == 404


@pytest.mark.anyio
async def test_chat_invalid_mode_returns_422(client):
    response = await client.post(
        "/api/barrier-intel/chat",
        json={
            "session_id": "any-id",
            "user_question": "What if I had a car?",
            "mode": "what_if",
        },
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Cycle 5: guardrail short-circuit + SSE content-type
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_chat_guardrail_returns_sse_stream(client):
    """Disallowed topic triggers guardrail — still returns SSE, no Claude call."""
    response = await client.post(
        "/api/barrier-intel/chat",
        json={
            "session_id": "any-id",
            "user_question": "Can I sue my employer for wrongful termination?",
            "mode": "next_steps",
        },
    )
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    assert "done" in response.text


def _make_fake_store():
    from unittest.mock import MagicMock

    from app.rag.store import RagStore

    store = RagStore(index_dir=None)
    store.index = MagicMock()
    store.index.ntotal = 0
    store.metadata = []
    return store


@pytest.mark.anyio
async def test_chat_returns_sse_for_valid_session(client, test_engine):
    """Valid session + allowed topic → SSE stream (Claude mocked)."""
    import json as _j
    from unittest.mock import AsyncMock, MagicMock, patch

    from app.core.database import get_async_session_factory
    from app.core.queries import create_session

    factory = get_async_session_factory()
    async with factory() as db:
        session_id = await create_session(
            db,
            session_data={
                "barriers": _j.dumps(["CHILDCARE_EVENING"]),
                "qualifications": "",
                "profile": _j.dumps({"zip_code": "36104"}),
            },
        )

    async def _fake_llm_stream(prompt: str):
        yield "Here are your next steps.", 0, 0
        yield "", 100, 50

    with patch("app.barrier_intel.llm_client.get_llm_stream", side_effect=_fake_llm_stream), \
         patch("app.barrier_intel.stream.get_llm_stream", side_effect=_fake_llm_stream), \
         patch("app.routes.barrier_intel.get_rag_store", return_value=_make_fake_store()):
        response = await client.post(
            "/api/barrier-intel/chat",
            json={"session_id": session_id, "user_question": "What to do?", "mode": "next_steps"},
        )

    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    assert "done" in response.text

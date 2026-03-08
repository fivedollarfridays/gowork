"""Tests for T24.8 — multi-provider LLM configuration and client factory."""

import pytest


# ---------------------------------------------------------------------------
# Cycle 1: Config fields
# ---------------------------------------------------------------------------

def test_config_default_provider_is_anthropic():
    from app.core.config import Settings
    s = Settings(anthropic_api_key="test-key")
    assert s.llm_provider == "anthropic"


def test_config_accepts_openai_provider():
    from app.core.config import Settings
    s = Settings(llm_provider="openai", openai_api_key="sk-test")
    assert s.llm_provider == "openai"
    assert s.openai_api_key == "sk-test"
    assert s.openai_model == "gpt-4o"


def test_config_accepts_gemini_provider():
    from app.core.config import Settings
    s = Settings(llm_provider="gemini", gemini_api_key="gm-test")
    assert s.llm_provider == "gemini"
    assert s.gemini_api_key == "gm-test"
    assert s.gemini_model == "gemini-2.0-flash"


# ---------------------------------------------------------------------------
# Cycle 2: llm_client factory — Anthropic (default)
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_anthropic_stream_yields_text_and_tokens():
    from unittest.mock import AsyncMock, MagicMock, patch
    from app.barrier_intel.llm_client import get_llm_stream

    mock_stream = MagicMock()
    mock_stream.__aenter__ = AsyncMock(return_value=mock_stream)
    mock_stream.__aexit__ = AsyncMock(return_value=None)

    async def _tokens():
        yield "Hello "
        yield "world"

    mock_stream.text_stream = _tokens()
    mock_final = MagicMock()
    mock_final.usage.input_tokens = 10
    mock_final.usage.output_tokens = 5
    mock_stream.get_final_message = AsyncMock(return_value=mock_final)

    with patch("app.barrier_intel.llm_client.AsyncAnthropic") as mock_cls:
        mock_cls.return_value.messages.stream.return_value = mock_stream
        results = []
        async for text, in_tok, out_tok in get_llm_stream("test prompt"):
            results.append((text, in_tok, out_tok))

    texts = [r[0] for r in results if r[0]]
    assert "Hello " in texts
    assert "world" in texts
    final = [r for r in results if r[1] > 0]
    assert final[0][1] == 10
    assert final[0][2] == 5


# ---------------------------------------------------------------------------
# Cycle 3: OpenAI + Gemini providers + missing key validation
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_openai_stream_yields_text():
    from unittest.mock import AsyncMock, MagicMock, patch
    from app.barrier_intel.llm_client import _openai_stream

    async def _chunks():
        chunk1 = MagicMock()
        chunk1.choices = [MagicMock()]
        chunk1.choices[0].delta.content = "Step 1"
        chunk1.usage = None
        yield chunk1
        chunk2 = MagicMock()
        chunk2.choices = [MagicMock()]
        chunk2.choices[0].delta.content = None
        chunk2.usage = MagicMock(prompt_tokens=20, completion_tokens=8)
        yield chunk2

    with patch("openai.AsyncOpenAI") as mock_cls:
        mock_cls.return_value.chat.completions.create = AsyncMock(return_value=_chunks())
        results = []
        async for text, in_tok, out_tok in _openai_stream("test"):
            results.append((text, in_tok, out_tok))

    assert any(r[0] == "Step 1" for r in results)
    assert any(r[1] == 20 for r in results)


@pytest.mark.anyio
async def test_gemini_stream_yields_text():
    from unittest.mock import AsyncMock, MagicMock, patch
    from app.barrier_intel.llm_client import _gemini_stream

    async def _chunks():
        c = MagicMock()
        c.text = "Gemini reply"
        yield c

    with patch("google.genai.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.aio.models.generate_content_stream = AsyncMock(return_value=_chunks())

        results = []
        async for text, _, __ in _gemini_stream("test"):
            results.append(text)

    assert "Gemini reply" in results


def test_missing_api_key_raises_value_error():
    from app.barrier_intel.llm_client import get_llm_stream
    from app.core.config import Settings
    from unittest.mock import patch

    settings = Settings(llm_provider="openai", openai_api_key="")
    with patch("app.barrier_intel.llm_client.get_settings", return_value=settings):
        with pytest.raises(ValueError, match="OPENAI_API_KEY"):
            get_llm_stream("test")


def test_unknown_provider_raises_value_error():
    from app.barrier_intel.llm_client import get_llm_stream
    from app.core.config import Settings
    from unittest.mock import patch

    settings = Settings(llm_provider="cohere")
    with patch("app.barrier_intel.llm_client.get_settings", return_value=settings):
        with pytest.raises(ValueError, match="Unknown LLM_PROVIDER"):
            get_llm_stream("test")

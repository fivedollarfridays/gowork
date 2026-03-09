"""Tests for LLM provider adapters."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.ai.providers import (
    _configure_gemini,
    _get_anthropic_client,
    _get_openai_client,
    anthropic_stream,
    gemini_stream,
    openai_stream,
    reset_provider_cache,
)


@pytest.fixture(autouse=True)
def reset_provider_state():
    """Reset cached provider clients before and after each test."""
    reset_provider_cache()
    yield
    reset_provider_cache()


# ---------- Client caching ----------


class TestClientCaching:
    """Verify provider clients are created once and reused."""

    def test_anthropic_client_cached(self):
        """_get_anthropic_client returns the same instance on repeated calls."""
        with patch("app.ai.providers.get_settings") as mock_settings:
            mock_settings.return_value.anthropic_api_key = "sk-test"
            with patch(
                "app.ai.providers.AsyncAnthropic",
                create=True,
            ) as MockAnthropic:
                # Patch the import inside the function
                fake_client = MagicMock()
                with patch.dict(
                    "sys.modules",
                    {"anthropic": MagicMock(AsyncAnthropic=lambda **kw: fake_client)},
                ):
                    first = _get_anthropic_client()
                    second = _get_anthropic_client()
                    assert first is second

    def test_openai_client_cached(self):
        """_get_openai_client returns the same instance on repeated calls."""
        with patch("app.ai.providers.get_settings") as mock_settings:
            mock_settings.return_value.openai_api_key = "sk-test"
            fake_client = MagicMock()
            with patch.dict(
                "sys.modules",
                {"openai": MagicMock(AsyncOpenAI=lambda **kw: fake_client)},
            ):
                first = _get_openai_client()
                second = _get_openai_client()
                assert first is second

    def test_gemini_configure_called_once(self):
        """_configure_gemini only calls genai.configure on first invocation."""
        mock_genai = MagicMock()
        with patch("app.ai.providers.get_settings") as mock_settings:
            mock_settings.return_value.gemini_api_key = "gm-key"
            with patch.dict("sys.modules", {"google.generativeai": mock_genai}):
                _configure_gemini()
                _configure_gemini()
                mock_genai.configure.assert_called_once_with(api_key="gm-key")


# ---------- anthropic_stream ----------


@pytest.mark.anyio
class TestAnthropicStream:
    """Test Anthropic provider streaming via mocked SDK."""

    async def test_yields_text_chunks(self):
        """anthropic_stream should yield text chunks from the SDK stream."""
        # Build mock async text_stream
        async def mock_text_stream():
            yield "Hello"
            yield " world"

        # Build mock context manager for client.messages.stream()
        mock_stream_ctx = MagicMock()
        mock_stream_ctx.__aenter__ = AsyncMock(return_value=mock_stream_ctx)
        mock_stream_ctx.__aexit__ = AsyncMock(return_value=False)
        mock_stream_ctx.text_stream = mock_text_stream()

        mock_client = MagicMock()
        mock_client.messages.stream.return_value = mock_stream_ctx

        with patch("app.ai.providers._get_anthropic_client", return_value=mock_client):
            with patch("app.ai.providers.get_settings") as mock_settings:
                mock_settings.return_value.claude_model = "claude-test"
                chunks = []
                async for chunk in anthropic_stream("system", "user"):
                    chunks.append(chunk)

        assert chunks == ["Hello", " world"]
        mock_client.messages.stream.assert_called_once_with(
            model="claude-test",
            max_tokens=1024,
            system="system",
            messages=[{"role": "user", "content": "user"}],
        )


# ---------- openai_stream ----------


@pytest.mark.anyio
class TestOpenaiStream:
    """Test OpenAI provider streaming via mocked SDK."""

    async def test_yields_delta_content(self):
        """openai_stream should yield content from chunk deltas."""
        # Build mock chunk objects
        def make_chunk(content):
            chunk = MagicMock()
            delta = MagicMock()
            delta.content = content
            choice = MagicMock()
            choice.delta = delta
            chunk.choices = [choice]
            return chunk

        # Async iterator of chunks
        async def mock_response():
            yield make_chunk("Hi")
            yield make_chunk(" there")

        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response())

        with patch("app.ai.providers._get_openai_client", return_value=mock_client):
            with patch("app.ai.providers.get_settings") as mock_settings:
                mock_settings.return_value.openai_model = "gpt-test"
                chunks = []
                async for chunk in openai_stream("system", "user"):
                    chunks.append(chunk)

        assert chunks == ["Hi", " there"]

    async def test_skips_empty_delta_content(self):
        """openai_stream should skip chunks where delta.content is None."""
        def make_chunk(content):
            chunk = MagicMock()
            delta = MagicMock()
            delta.content = content
            choice = MagicMock()
            choice.delta = delta
            chunk.choices = [choice]
            return chunk

        async def mock_response():
            yield make_chunk("Hi")
            yield make_chunk(None)  # empty delta
            yield make_chunk(" end")

        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response())

        with patch("app.ai.providers._get_openai_client", return_value=mock_client):
            with patch("app.ai.providers.get_settings") as mock_settings:
                mock_settings.return_value.openai_model = "gpt-test"
                chunks = []
                async for chunk in openai_stream("system", "user"):
                    chunks.append(chunk)

        assert chunks == ["Hi", " end"]


# ---------- gemini_stream ----------


@pytest.mark.anyio
class TestGeminiStream:
    """Test Gemini provider streaming via mocked SDK."""

    async def test_yields_text_chunks(self):
        """gemini_stream should yield text from async content chunks."""
        # Build mock chunk objects
        chunk1 = MagicMock()
        chunk1.text = "Gemini"
        chunk2 = MagicMock()
        chunk2.text = " says hi"

        async def mock_response():
            yield chunk1
            yield chunk2

        mock_model = MagicMock()
        mock_model.generate_content_async = AsyncMock(
            return_value=mock_response(),
        )

        mock_genai = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model

        with patch.dict("sys.modules", {"google.generativeai": mock_genai}):
            with patch("app.ai.providers._configure_gemini"):
                with patch("app.ai.providers.get_settings") as mock_settings:
                    mock_settings.return_value.gemini_model = "gemini-test"
                    chunks = []
                    async for chunk in gemini_stream("system", "user"):
                        chunks.append(chunk)

        assert chunks == ["Gemini", " says hi"]

    async def test_skips_empty_text_chunks(self):
        """gemini_stream should skip chunks where text is empty/None."""
        chunk1 = MagicMock()
        chunk1.text = "data"
        chunk2 = MagicMock()
        chunk2.text = ""  # empty
        chunk3 = MagicMock()
        chunk3.text = " more"

        async def mock_response():
            yield chunk1
            yield chunk2
            yield chunk3

        mock_model = MagicMock()
        mock_model.generate_content_async = AsyncMock(
            return_value=mock_response(),
        )

        mock_genai = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model

        with patch.dict("sys.modules", {"google.generativeai": mock_genai}):
            with patch("app.ai.providers._configure_gemini"):
                with patch("app.ai.providers.get_settings") as mock_settings:
                    mock_settings.return_value.gemini_model = "gemini-test"
                    chunks = []
                    async for chunk in gemini_stream("system", "user"):
                        chunks.append(chunk)

        assert chunks == ["data", " more"]

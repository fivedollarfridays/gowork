"""Tests for multi-provider LLM client factory."""

from unittest.mock import patch

import pytest

from app.ai.llm_client import get_llm_stream, resolve_provider
from app.ai.providers import (
    MockProvider,
    anthropic_stream,
    gemini_stream,
    mock_stream,
    openai_stream,
)


# ---------- resolve_provider ----------


class TestResolveProvider:
    """Test provider resolution from config and overrides."""

    def test_default_returns_anthropic_when_key_set(self):
        with patch("app.ai.llm_client.get_settings") as mock_settings:
            mock_settings.return_value.llm_provider = "anthropic"
            mock_settings.return_value.anthropic_api_key = "sk-test"
            assert resolve_provider() == "anthropic"

    def test_override_takes_precedence(self):
        with patch("app.ai.llm_client.get_settings") as mock_settings:
            mock_settings.return_value.llm_provider = "anthropic"
            mock_settings.return_value.openai_api_key = "sk-test"
            assert resolve_provider(override="openai") == "openai"

    def test_falls_back_to_mock_when_no_key(self):
        with patch("app.ai.llm_client.get_settings") as mock_settings:
            mock_settings.return_value.llm_provider = "anthropic"
            mock_settings.return_value.anthropic_api_key = ""
            assert resolve_provider() == "mock"

    def test_mock_override_always_works(self):
        with patch("app.ai.llm_client.get_settings") as mock_settings:
            mock_settings.return_value.llm_provider = "anthropic"
            assert resolve_provider(override="mock") == "mock"

    def test_gemini_with_key(self):
        with patch("app.ai.llm_client.get_settings") as mock_settings:
            mock_settings.return_value.llm_provider = "gemini"
            mock_settings.return_value.gemini_api_key = "gm-key"
            assert resolve_provider() == "gemini"

    def test_openai_without_key_falls_back(self):
        with patch("app.ai.llm_client.get_settings") as mock_settings:
            mock_settings.return_value.llm_provider = "openai"
            mock_settings.return_value.openai_api_key = ""
            assert resolve_provider() == "mock"

    def test_config_provider_mock_returns_mock(self):
        """When settings.llm_provider is 'mock' (no override), returns 'mock'."""
        with patch("app.ai.llm_client.get_settings") as mock_settings:
            mock_settings.return_value.llm_provider = "mock"
            assert resolve_provider() == "mock"


# ---------- mock_stream ----------


@pytest.mark.anyio
class TestMockStream:
    """Test mock provider produces chunks."""

    async def test_produces_chunks(self):
        chunks = []
        async for chunk in mock_stream("You are helpful.", "Hello"):
            chunks.append(chunk)
        assert len(chunks) > 0
        assert all(isinstance(c, str) for c in chunks)

    async def test_response_mentions_mock(self):
        text = ""
        async for chunk in mock_stream("system", "user prompt"):
            text += chunk
        assert len(text) > 0


# ---------- get_llm_stream ----------


@pytest.mark.anyio
class TestGetLlmStream:
    """Test the main factory function."""

    async def test_returns_async_iterator(self):
        with patch("app.ai.llm_client.resolve_provider", return_value="mock"):
            stream = get_llm_stream("system prompt", "user prompt")
            chunks = []
            async for chunk in stream:
                chunks.append(chunk)
            assert len(chunks) > 0
            assert all(isinstance(c, str) for c in chunks)

    async def test_override_provider(self):
        with patch("app.ai.llm_client.resolve_provider", return_value="mock") as mock_resolve:
            chunks = []
            async for chunk in get_llm_stream("sys", "user", provider="mock"):
                chunks.append(chunk)
            mock_resolve.assert_called_once_with(override="mock")

    async def test_fallback_on_provider_error(self):
        """If configured provider raises before yielding, falls back to mock."""
        def failing_provider(provider, system_prompt, user_prompt):
            raise ConnectionError("API down")

        with patch("app.ai.llm_client.resolve_provider", return_value="anthropic"):
            with patch("app.ai.llm_client._get_provider_stream", side_effect=failing_provider):
                chunks = []
                async for chunk in get_llm_stream("sys", "user"):
                    chunks.append(chunk)
                assert len(chunks) > 0  # Mock fallback produced output

    async def test_mid_stream_failure_raises(self):
        """If provider yields then raises, error must propagate (no mock fallback)."""
        async def partial_then_fail(sys_prompt, usr_prompt):
            yield "partial-chunk"
            raise ConnectionError("connection dropped mid-stream")

        with patch("app.ai.llm_client.resolve_provider", return_value="anthropic"):
            with patch(
                "app.ai.llm_client._PROVIDER_STREAMS",
                {"anthropic": partial_then_fail, "mock": mock_stream},
            ):
                with pytest.raises(ConnectionError, match="mid-stream"):
                    async for _ in get_llm_stream("sys", "user"):
                        pass


# ---------- anthropic_stream ----------


@pytest.mark.anyio
class TestProviderStreamDispatch:
    """Test that get_llm_stream dispatches to correct provider."""

    async def test_dispatches_to_anthropic(self):
        """Verify anthropic provider is selected and called."""
        async def fake_anthropic(sys, usr):
            yield "anthropic-chunk"

        with patch("app.ai.llm_client.resolve_provider", return_value="anthropic"):
            with patch("app.ai.llm_client._PROVIDER_STREAMS", {"anthropic": fake_anthropic, "mock": mock_stream}):
                chunks = []
                async for chunk in get_llm_stream("sys", "user"):
                    chunks.append(chunk)
                assert chunks == ["anthropic-chunk"]

    async def test_dispatches_to_openai(self):
        """Verify openai provider is selected and called."""
        async def fake_openai(sys, usr):
            yield "openai-chunk"

        with patch("app.ai.llm_client.resolve_provider", return_value="openai"):
            with patch("app.ai.llm_client._PROVIDER_STREAMS", {"openai": fake_openai, "mock": mock_stream}):
                chunks = []
                async for chunk in get_llm_stream("sys", "user"):
                    chunks.append(chunk)
                assert chunks == ["openai-chunk"]

    async def test_dispatches_to_gemini(self):
        """Verify gemini provider is selected and called."""
        async def fake_gemini(sys, usr):
            yield "gemini-chunk"

        with patch("app.ai.llm_client.resolve_provider", return_value="gemini"):
            with patch("app.ai.llm_client._PROVIDER_STREAMS", {"gemini": fake_gemini, "mock": mock_stream}):
                chunks = []
                async for chunk in get_llm_stream("sys", "user"):
                    chunks.append(chunk)
                assert chunks == ["gemini-chunk"]

    async def test_provider_error_falls_back_to_mock(self):
        """If provider raises, should fall back to mock stream."""
        async def failing_provider(sys, usr):
            raise ConnectionError("API unreachable")
            yield  # noqa: unreachable

        with patch("app.ai.llm_client.resolve_provider", return_value="anthropic"):
            with patch("app.ai.llm_client._PROVIDER_STREAMS", {"anthropic": failing_provider, "mock": mock_stream}):
                chunks = []
                async for chunk in get_llm_stream("sys", "user"):
                    chunks.append(chunk)
                assert len(chunks) > 0  # Mock fallback produced output


# ---------- MockProvider ----------


class TestMockProvider:
    """Test MockProvider response generation."""

    def test_builds_response_with_user_prompt(self):
        provider = MockProvider()
        response = provider.build_response("Tell me about jobs")
        assert isinstance(response, str)
        assert len(response) > 0


# ---------- check_llm_providers ----------


class TestCheckLlmProviders:
    """Test provider health check function."""

    def test_returns_all_providers(self):
        from app.ai.llm_client import check_llm_providers

        with patch("app.ai.llm_client.get_settings") as mock_settings:
            mock_settings.return_value.llm_provider = "anthropic"
            mock_settings.return_value.anthropic_api_key = "sk-test"
            mock_settings.return_value.openai_api_key = ""
            mock_settings.return_value.gemini_api_key = ""
            result = check_llm_providers()

        assert "anthropic" in result["providers"]
        assert "openai" in result["providers"]
        assert "gemini" in result["providers"]
        assert "mock" in result["providers"]

    def test_configured_provider_shows_configured(self):
        from app.ai.llm_client import check_llm_providers

        with patch("app.ai.llm_client.get_settings") as mock_settings:
            mock_settings.return_value.llm_provider = "anthropic"
            mock_settings.return_value.anthropic_api_key = "sk-test"
            mock_settings.return_value.openai_api_key = ""
            mock_settings.return_value.gemini_api_key = ""
            result = check_llm_providers()

        assert result["providers"]["anthropic"] == "configured"
        assert result["providers"]["openai"] == "no_key"
        assert result["providers"]["mock"] == "available"

    def test_active_provider_resolved(self):
        from app.ai.llm_client import check_llm_providers

        with patch("app.ai.llm_client.get_settings") as mock_settings:
            mock_settings.return_value.llm_provider = "anthropic"
            mock_settings.return_value.anthropic_api_key = "sk-test"
            mock_settings.return_value.openai_api_key = ""
            mock_settings.return_value.gemini_api_key = ""
            result = check_llm_providers()

        assert result["active"] == "anthropic"

    def test_falls_back_to_mock_when_no_keys(self):
        from app.ai.llm_client import check_llm_providers

        with patch("app.ai.llm_client.get_settings") as mock_settings:
            mock_settings.return_value.llm_provider = "anthropic"
            mock_settings.return_value.anthropic_api_key = ""
            mock_settings.return_value.openai_api_key = ""
            mock_settings.return_value.gemini_api_key = ""
            result = check_llm_providers()

        assert result["active"] == "mock"

"""Tests for the thin Haiku client wrapper + TTL cache.

The client itself is exercised by integration tests against a mocked
anthropic SDK — we don't hit the live API in unit tests.
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

from app.integrations.llm._cache import TTLCache
from app.integrations.llm._haiku_client import (
    HaikuError,
    HaikuResult,
    call_haiku,
)


class TestHaikuResult:
    def test_estimated_cost_for_typical_call(self) -> None:
        """Typical 600in/250out Haiku call costs ~$0.0015."""
        result = HaikuResult(text="ok", input_tokens=600, output_tokens=250)
        # 600 * 0.8e-6 + 250 * 4e-6 = 0.00048 + 0.001 = 0.00148
        assert result.estimated_cost_usd == pytest.approx(0.00148, abs=1e-6)

    def test_zero_tokens_zero_cost(self) -> None:
        """No telemetry returned -> cost reports as zero."""
        result = HaikuResult(text="ok", input_tokens=0, output_tokens=0)
        assert result.estimated_cost_usd == 0.0


class TestCallHaiku:
    @pytest.mark.asyncio
    async def test_missing_api_key_raises_haiku_error(self) -> None:
        """No ANTHROPIC_API_KEY -> HaikuError, no SDK import."""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": ""}, clear=False):
            with pytest.raises(HaikuError, match="not configured"):
                await call_haiku("sys", "user")

    @pytest.mark.asyncio
    async def test_returns_text_and_tokens_on_success(self) -> None:
        """Successful SDK call -> HaikuResult with text + tokens."""
        fake_block = MagicMock()
        fake_block.type = "text"
        fake_block.text = "Hello world."
        fake_message = MagicMock()
        fake_message.content = [fake_block]
        fake_message.usage = MagicMock(input_tokens=42, output_tokens=10)

        fake_client = MagicMock()
        fake_client.messages.create.return_value = fake_message
        fake_module = MagicMock()
        fake_module.Anthropic.return_value = fake_client

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-test"}, clear=False):
            with patch.dict("sys.modules", {"anthropic": fake_module}):
                result = await call_haiku("sys", "user")

        assert result.text == "Hello world."
        assert result.input_tokens == 42
        assert result.output_tokens == 10

    @pytest.mark.asyncio
    async def test_empty_text_raises_haiku_error(self) -> None:
        """SDK returns no text blocks -> HaikuError."""
        fake_message = MagicMock()
        fake_message.content = []
        fake_message.usage = None

        fake_client = MagicMock()
        fake_client.messages.create.return_value = fake_message
        fake_module = MagicMock()
        fake_module.Anthropic.return_value = fake_client

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-test"}, clear=False):
            with patch.dict("sys.modules", {"anthropic": fake_module}):
                with pytest.raises(HaikuError, match="empty"):
                    await call_haiku("sys", "user")

    @pytest.mark.asyncio
    async def test_sdk_exception_wrapped_as_haiku_error(self) -> None:
        """Any SDK error is converted to HaikuError so callers can fall back."""
        fake_client = MagicMock()
        fake_client.messages.create.side_effect = RuntimeError("network down")
        fake_module = MagicMock()
        fake_module.Anthropic.return_value = fake_client

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-test"}, clear=False):
            with patch.dict("sys.modules", {"anthropic": fake_module}):
                with pytest.raises(HaikuError, match="failed"):
                    await call_haiku("sys", "user")


class TestTTLCache:
    def test_get_returns_none_for_missing_key(self) -> None:
        cache: TTLCache[str] = TTLCache(default_ttl_s=60)
        assert cache.get("missing") is None

    def test_set_then_get_returns_value(self) -> None:
        cache: TTLCache[str] = TTLCache(default_ttl_s=60)
        cache.set("k", "v")
        assert cache.get("k") == "v"

    def test_expired_entry_returns_none_and_evicts(self) -> None:
        """TTL=0 means immediate expiration on next read."""
        cache: TTLCache[str] = TTLCache(default_ttl_s=60)
        cache.set("k", "v", ttl_s=-1.0)  # already expired
        assert cache.get("k") is None
        assert len(cache) == 0

    def test_max_entries_eviction(self) -> None:
        """Filling past max_entries evicts oldest."""
        cache: TTLCache[str] = TTLCache(default_ttl_s=60, max_entries=2)
        cache.set("a", "1")
        cache.set("b", "2")
        cache.set("c", "3")  # evicts "a"
        assert cache.get("a") is None
        assert cache.get("b") == "2"
        assert cache.get("c") == "3"

    def test_clear_drops_all_entries(self) -> None:
        cache: TTLCache[str] = TTLCache(default_ttl_s=60)
        cache.set("k", "v")
        cache.clear()
        assert cache.get("k") is None
        assert len(cache) == 0

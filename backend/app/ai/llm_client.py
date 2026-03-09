"""Multi-provider LLM client factory.

Prompt-agnostic: accepts system_prompt and user_prompt parameters,
making it reusable across barrier intel chat and narrative generation.
"""

import logging
from collections.abc import AsyncIterator

from app.ai.providers import anthropic_stream, gemini_stream, mock_stream, openai_stream
from app.core.config import get_settings

logger = logging.getLogger(__name__)

# Provider → required config key
_PROVIDER_KEYS = {
    "anthropic": "anthropic_api_key",
    "openai": "openai_api_key",
    "gemini": "gemini_api_key",
    "mock": None,
}

# Provider → stream function
_PROVIDER_STREAMS = {
    "anthropic": anthropic_stream,
    "openai": openai_stream,
    "gemini": gemini_stream,
    "mock": mock_stream,
}


def resolve_provider(override: str | None = None) -> str:
    """Determine which LLM provider to use.

    Priority: override > config > fallback to mock if key missing.
    """
    if override == "mock":
        return "mock"

    settings = get_settings()
    provider = override or settings.llm_provider

    if provider == "mock":
        return "mock"

    key_attr = _PROVIDER_KEYS.get(provider)
    if key_attr and not getattr(settings, key_attr, ""):
        logger.warning("No API key for provider '%s', falling back to mock", provider)
        return "mock"

    return provider


def _get_provider_stream(
    provider: str, system_prompt: str, user_prompt: str,
) -> AsyncIterator[str]:
    """Get the streaming function for a provider."""
    stream_fn = _PROVIDER_STREAMS.get(provider, mock_stream)
    return stream_fn(system_prompt, user_prompt)


def check_llm_providers() -> dict:
    """Check which LLM providers are configured and return status info."""
    settings = get_settings()
    statuses = {}
    for provider, key_attr in _PROVIDER_KEYS.items():
        if provider == "mock":
            statuses["mock"] = "available"
        elif key_attr and getattr(settings, key_attr, ""):
            statuses[provider] = "configured"
        else:
            statuses[provider] = "no_key"
    active = resolve_provider()
    return {"providers": statuses, "active": active}


async def get_llm_stream(
    system_prompt: str,
    user_prompt: str,
    provider: str | None = None,
) -> AsyncIterator[str]:
    """Stream LLM response chunks. Falls back to mock on failure.

    Args:
        system_prompt: System instruction for the LLM.
        user_prompt: User message content.
        provider: Override provider name (anthropic/openai/gemini/mock).

    Yields:
        String chunks of the LLM response.
    """
    resolved = resolve_provider(override=provider)

    if resolved != "mock":
        yielded = False
        try:
            async for chunk in _get_provider_stream(resolved, system_prompt, user_prompt):
                yielded = True
                yield chunk
            return
        except (ConnectionError, TimeoutError, OSError, RuntimeError):
            if yielded:
                raise  # Mid-stream failure: don't mask with mock
            logger.warning(
                "Provider '%s' failed, falling back to mock", resolved, exc_info=True,
            )

    async for chunk in mock_stream(system_prompt, user_prompt):
        yield chunk

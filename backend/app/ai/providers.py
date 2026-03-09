"""LLM provider adapters — each returns an async iterator of string chunks."""

import logging
from collections.abc import AsyncIterator

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# Cached client instances (created lazily, reused across requests)
_anthropic_client = None
_openai_client = None
_gemini_configured = False


class MockProvider:
    """Mock LLM provider for testing and graceful degradation."""

    def build_response(self, user_prompt: str) -> str:
        """Build a canned response without calling any API."""
        return (
            "I understand you're asking about support resources in Montgomery. "
            "While I'm currently running in offline mode, here are some general steps: "
            "1) Visit the Alabama Career Center on Carter Hill Road for personalized guidance. "
            "2) Check with local community organizations for additional support. "
            "3) Review your personalized plan for specific action items."
        )


async def mock_stream(system_prompt: str, user_prompt: str) -> AsyncIterator[str]:
    """Yield chunks from the mock provider."""
    provider = MockProvider()
    response = provider.build_response(user_prompt)
    # Simulate streaming by splitting into word-sized chunks
    words = response.split(" ")
    for i, word in enumerate(words):
        yield word if i == 0 else f" {word}"


def _get_anthropic_client():
    """Get or create cached Anthropic client."""
    global _anthropic_client
    if _anthropic_client is None:
        from anthropic import AsyncAnthropic
        settings = get_settings()
        _anthropic_client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    return _anthropic_client


def _get_openai_client():
    """Get or create cached OpenAI client."""
    global _openai_client
    if _openai_client is None:
        from openai import AsyncOpenAI
        settings = get_settings()
        _openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _openai_client


def _configure_gemini():
    """Configure Gemini SDK once (global state)."""
    global _gemini_configured
    if not _gemini_configured:
        import google.generativeai as genai
        settings = get_settings()
        genai.configure(api_key=settings.gemini_api_key)
        _gemini_configured = True


async def anthropic_stream(system_prompt: str, user_prompt: str) -> AsyncIterator[str]:
    """Stream from the Anthropic (Claude) API."""
    settings = get_settings()
    client = _get_anthropic_client()
    async with client.messages.stream(
        model=settings.claude_model,
        max_tokens=1024,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    ) as stream:
        async for text in stream.text_stream:
            yield text


async def openai_stream(system_prompt: str, user_prompt: str) -> AsyncIterator[str]:
    """Stream from the OpenAI API."""
    settings = get_settings()
    client = _get_openai_client()
    response = await client.chat.completions.create(
        model=settings.openai_model,
        stream=True,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    async for chunk in response:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


async def gemini_stream(system_prompt: str, user_prompt: str) -> AsyncIterator[str]:
    """Stream from the Google Gemini API."""
    import google.generativeai as genai

    _configure_gemini()
    settings = get_settings()
    model = genai.GenerativeModel(
        settings.gemini_model,
        system_instruction=system_prompt,
    )
    response = await model.generate_content_async(
        user_prompt,
        stream=True,
    )
    async for chunk in response:
        if chunk.text:
            yield chunk.text

"""Provider-agnostic LLM streaming client factory.

Supports: anthropic (default) | openai | gemini
Controlled via LLM_PROVIDER env var.
"""

from anthropic import AsyncAnthropic

from app.barrier_intel.prompts import SYSTEM_PROMPT
from app.core.config import get_settings


async def _anthropic_stream(prompt: str):
    settings = get_settings()
    client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    async with client.messages.stream(
        model=settings.claude_model,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        async for text in stream.text_stream:
            yield text, 0, 0
        final = await stream.get_final_message()
        yield "", final.usage.input_tokens, final.usage.output_tokens


async def _openai_stream(prompt: str):
    from openai import AsyncOpenAI
    settings = get_settings()
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    stream = await client.chat.completions.create(
        model=settings.openai_model,
        max_tokens=1024,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        stream=True,
        stream_options={"include_usage": True},
    )
    input_tokens = output_tokens = 0
    async for chunk in stream:
        delta = chunk.choices[0].delta.content if chunk.choices else None
        if delta:
            yield delta, 0, 0
        if chunk.usage:
            input_tokens = chunk.usage.prompt_tokens
            output_tokens = chunk.usage.completion_tokens
    yield "", input_tokens, output_tokens


async def _gemini_stream(prompt: str):
    from google import genai
    from google.genai import types
    settings = get_settings()
    client = genai.Client(api_key=settings.gemini_api_key)
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        max_output_tokens=1024,
    )
    async for chunk in await client.aio.models.generate_content_stream(
        model=settings.gemini_model,
        contents=prompt,
        config=config,
    ):
        text = chunk.text if chunk.text else ""
        if text:
            yield text, 0, 0
    yield "", 0, 0


_PROVIDERS = {
    "anthropic": _anthropic_stream,
    "openai": _openai_stream,
    "gemini": _gemini_stream,
}


def get_llm_stream(prompt: str):
    """Return the async generator for the configured LLM provider."""
    settings = get_settings()
    provider = settings.llm_provider
    if provider not in _PROVIDERS:
        raise ValueError(
            f"Unknown LLM_PROVIDER '{provider}'. Choose: {', '.join(_PROVIDERS)}"
        )
    _validate_key(settings, provider)
    return _PROVIDERS[provider](prompt)


def _validate_key(settings, provider: str) -> None:
    keys = {
        "anthropic": settings.anthropic_api_key,
        "openai": settings.openai_api_key,
        "gemini": settings.gemini_api_key,
    }
    if not keys[provider]:
        raise ValueError(
            f"LLM_PROVIDER is '{provider}' but the corresponding API key is not set. "
            f"Set {'ANTHROPIC_API_KEY' if provider == 'anthropic' else provider.upper() + '_API_KEY'} in your .env"
        )

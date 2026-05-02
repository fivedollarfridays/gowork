"""Thin non-streaming Haiku client for short, structured calls.

The streaming `app.ai.llm_client` is the right tool for long narratives.
For 2-paragraph explanations / 3-bullet summaries / single-sentence
reframes, we want a one-shot blocking call that returns a string.

Anthropic SDK is the only dependency.  When ANTHROPIC_API_KEY is missing
or the SDK call raises, callers MUST catch HaikuError and degrade.
"""

from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Configurable per-call cost ceiling.  Haiku is ~$0.80/Mtok input,
# ~$4/Mtok output.  Average call: ~600 in + ~250 out -> ~$0.0015.
# We log per-call cost when tokens are returned by the SDK.
_DEFAULT_MODEL = os.environ.get("CLAUDE_MODEL", "claude-haiku-4-5-20251001")
_DEFAULT_TIMEOUT_S = 12.0


class HaikuError(RuntimeError):
    """Raised when the Haiku call fails for any reason.

    Callers MUST catch this and fall back to deterministic output.
    """


@dataclass(frozen=True)
class HaikuResult:
    """One Haiku response + token telemetry."""

    text: str
    input_tokens: int
    output_tokens: int

    @property
    def estimated_cost_usd(self) -> float:
        """Rough Haiku 4.5 cost estimate in USD."""
        return (
            self.input_tokens * 0.0000008
            + self.output_tokens * 0.000004
        )


async def call_haiku(
    system: str,
    user: str,
    *,
    max_tokens: int = 600,
    timeout_s: float = _DEFAULT_TIMEOUT_S,
    model: str | None = None,
) -> HaikuResult:
    """Call Haiku once, return text + token usage.

    Wraps the blocking SDK call in asyncio.to_thread + a hard timeout.
    Raises HaikuError on missing key, timeout, network error, empty text.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        raise HaikuError("ANTHROPIC_API_KEY not configured")

    try:
        import anthropic  # type: ignore
    except ImportError as exc:  # pragma: no cover - env-dependent
        raise HaikuError("anthropic SDK not installed") from exc

    chosen_model = model or _DEFAULT_MODEL

    def _blocking_call() -> HaikuResult:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model=chosen_model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        text_parts = [
            block.text for block in message.content
            if getattr(block, "type", "") == "text"
        ]
        text = "".join(text_parts).strip()
        if not text:
            raise HaikuError("Haiku returned empty text")
        usage = getattr(message, "usage", None)
        in_tok = getattr(usage, "input_tokens", 0) if usage else 0
        out_tok = getattr(usage, "output_tokens", 0) if usage else 0
        return HaikuResult(text=text, input_tokens=in_tok, output_tokens=out_tok)

    try:
        return await asyncio.wait_for(
            asyncio.to_thread(_blocking_call), timeout=timeout_s,
        )
    except asyncio.TimeoutError as exc:
        raise HaikuError(f"Haiku call timed out after {timeout_s}s") from exc
    except HaikuError:
        raise
    except Exception as exc:  # noqa: BLE001 - catch-all -> HaikuError
        raise HaikuError(f"Haiku call failed: {exc}") from exc

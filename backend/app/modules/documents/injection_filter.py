"""Prompt-injection blocklist for worker free-text (T12.15).

The resume and cover-letter generators feed a small amount of
worker-supplied text (name, notes, summary, employer …) to the LLM.
Before we hand anything over we scan it against a blocklist of
well-known injection patterns:

* role-override directives ("ignore previous instructions", "system:")
* delimiter injection (``<|im_end|>``, ``</system>`` …)
* "you are now" / "forget everything" framing

When any field matches, the caller MUST fall back to the deterministic
template path and record the offending field for audit.

This module is intentionally pattern-only — no LLM call, no IO. The
blocklist is conservative: false-positives land the worker on the
template path, which is safe. False-negatives let injected text reach
the LLM, so we prefer the occasional over-trigger.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

__all__ = ["InjectionCheck", "check_for_injection"]


# ---------------------------------------------------------------------------
# Blocklist — compiled once at module load.
# ---------------------------------------------------------------------------
#
# Each entry is a case-insensitive regex. The list is deliberately
# conservative: we prefer occasional over-triggering (the template path
# is always available) to letting an injection reach the model.

_INJECTION_SOURCES: tuple[str, ...] = (
    r"\bignore\s+(?:all\s+|previous\s+|above\s+)?"
    r"(?:prior\s+|previous\s+|the\s+)?instructions?\b",
    r"\bdisregard\b[^.\n]{0,60}\b(?:instructions?|rules?)\b",
    r"(?m)^\s*system:\s",
    r"\brole\s*:\s*system\b",
    r"\byou\s+are\s+now\b",
    r"\bforget\s+(?:everything|all|what)\b",
    # Delimiter / chat-format injection.
    r"\n```\s*system",
    r"</\s*(?:system|instructions?|prompt)\s*>",
    r"<\|im_end\|>",
    r"<\|im_start\|>",
)

_INJECTION_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(src, re.IGNORECASE) for src in _INJECTION_SOURCES
)


# ---------------------------------------------------------------------------
# Public types.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class InjectionCheck:
    """Outcome of a single blocklist scan.

    ``clean`` is True when no field matched any pattern. Otherwise
    ``offending_field`` names the field (key) and ``matched_pattern``
    holds the source regex string so callers can log it.
    """

    clean: bool
    matched_pattern: str | None
    offending_field: str | None


# ---------------------------------------------------------------------------
# Public API.
# ---------------------------------------------------------------------------


def check_for_injection(fields: dict[str, str]) -> InjectionCheck:
    """Scan each ``(field_name, value)`` pair; first match wins.

    The scan preserves dict insertion order (CPython 3.7+). ``None``
    or empty values are skipped — nothing to match against.
    """
    for field_name, value in fields.items():
        if not value:
            continue
        text = str(value)
        for pattern in _INJECTION_PATTERNS:
            if pattern.search(text):
                return InjectionCheck(
                    clean=False,
                    matched_pattern=pattern.pattern,
                    offending_field=field_name,
                )
    return InjectionCheck(
        clean=True,
        matched_pattern=None,
        offending_field=None,
    )

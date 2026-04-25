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
    # ----- direct override family ("ignore previous instructions") -----
    r"\bignore\s+(?:all\s+|previous\s+|above\s+)?"
    r"(?:prior\s+|previous\s+|the\s+)?instructions?\b",
    r"\bignore\s+instruction\s+set\b",
    r"\bdisregard\b[^.\n]{0,60}\b(?:instructions?|rules?|safety)\b",
    # ----- role / mode framing -----
    r"(?m)^\s*system:\s",
    r"\brole\s*:\s*system\b",
    r"\byou\s+are\s+now\b",
    r"\byou\s+are\s+no\s+longer\b",
    r"\byou\s+are\s+not\s+an?\s+(?:ai|assistant)\b",
    r"\bpretend\s+(?:that\s+)?you\s+are\b",
    r"\bact\s+as\s+(?:a|an|the)\b",
    r"\bfrom\s+now\s+on\b",
    r"\bfrom\s+this\s+point\s+forward\b",
    r"\bforget\s+(?:everything|all|what)\b",
    # ----- well-known jailbreak / mode names -----
    r"\b(?:developer|admin|jailbreak|dan)\s+mode\b",
    # ----- output exfiltration -----
    r"\b(?:reveal|print|repeat|show|output|quote)\b[^.\n]{0,80}"
    r"\b(?:system\s+(?:prompt|message|instructions?)|"
    r"initial\s+(?:prompt|instructions?|message)|"
    r"prompt\s+(?:above|verbatim)|your\s+(?:prompt|instructions?))\b",
    r"\bwhat\s+were\s+you\s+told\b",
    # ----- tool / function injection -----
    r"\b(?:call|invoke|execute|use)\s+(?:the\s+)?"
    r"(?:function|tool|command)\b",
    # ----- delimiter / chat-format injection -----
    r"\n```\s*system",
    r"```\s*\n\s*system\s*:",
    r"</\s*(?:system|instructions?|prompt)\s*>",
    r"<\|im_end\|>",
    r"<\|im_start\|>",
    # ----- markdown / bracket role headers -----
    r"(?m)^\s*#{1,6}\s*system\s*:?",
    r"\[\s*(?:system|assistant|user\s+complete)\s*\]",
    # ----- boundary spoofing -----
    r"-{2,}\s*end\s+(?:user|prompt|input)\s*-{2,}",
    r"\bend\s+of\s+(?:prompt|user|input)\b",
    r"\bbegin\s+system(?:\s+message)?\b",
    # ----- structured-payload "role: system" inside JSON/YAML -----
    r'"role"\s*:\s*"system"',
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

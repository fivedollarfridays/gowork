"""Worker-voice post-processor (T12.14).

Ported from ``ops/lib/cover_letter_generator.py`` (``apply_voice_rules``,
``_strip_dashes``, ``_strip_hedges``, ``_strip_quotes``) and
``ops/lib/resume_generator.py`` (``apply_summary_voice_rules``,
``_strip_hyphens``). The MontGoWork re-implementation is **plain-spoken
worker voice** rather than Kevin-voice: no forced lowercasing, no
injected curse words. Output is markdown that downstream T12.15/T12.16
render to HTML and PDF via :mod:`app.core.pdf_renderer`.

Public API
----------
:func:`apply_worker_voice`
    Single entry point — idempotent, runs every voice rule in
    deterministic order.
:func:`flesch_kincaid_grade`
    Pure-Python F-K grade calculator (no new deps). The test suite
    asserts grade <9.0 on a fixed 5-sample corpus after voice rules.

Dignity contract
----------------
Loaded labels (``ex-offender``, ``felon``, ``convict``, ``inmate``)
are **filtered** rather than substituted because the replacement is
context-dependent. Callers that need a fair-chance framing should
assemble one explicitly; this module refuses to guess.
"""

from __future__ import annotations

import re

__all__ = ["apply_worker_voice", "flesch_kincaid_grade"]


# ---------------------------------------------------------------------------
# Regexes — compiled once at module load.
# ---------------------------------------------------------------------------

# Em-dash (U+2014) or en-dash (U+2013) used as a sentence-break aside.
_DASH_RE = re.compile(r"\s*[—–]\s*")

# Hedge vocabulary — conservative list, word-boundary anchored so
# "mightier" survives the "might" rule.
_HEDGE_WORDS = ("perhaps", "maybe", "might", "possibly", "somewhat")
_HEDGE_PATTERNS = tuple(
    re.compile(rf"\b{w}\b", re.IGNORECASE) for w in _HEDGE_WORDS
)

# Smart quotes rewrite to ASCII.
_SMART_QUOTES = {"“": '"', "”": '"', "‘": "'", "’": "'"}

# Common-noun hyphens (lowercase-lowercase) get spaced. Proper-name
# hyphens (capital/digit on either side) are left alone.
_LOWER_HYPHEN_RE = re.compile(r"([a-z])-([a-z])")

# Loaded labels filtered from output. Hyphen- and space-separated
# variants both caught; trailing punctuation is swallowed so the
# surrounding sentence is not left with stray commas.
_DIGNITY_FILTERS = (
    re.compile(r"\bex[-\s]offenders?\b[,;:]?\s*", re.IGNORECASE),
    re.compile(r"\bfelons?\b[,;:]?\s*", re.IGNORECASE),
    re.compile(r"\bconvicts?\b[,;:]?\s*", re.IGNORECASE),
    re.compile(r"\binmates?\b[,;:]?\s*", re.IGNORECASE),
)

# Housekeeping.
_MULTI_SPACE_RE = re.compile(r"[ \t]{2,}")
_SPACE_BEFORE_PUNCT_RE = re.compile(r"\s+([.,!?;:])")
_VOWEL_GROUP_RE = re.compile(r"[aeiouy]+")
_WORD_RE = re.compile(r"\w+")
_SENTENCE_END_RE = re.compile(r"[.!?]+")
_ORPHAN_AS_AN_RE = re.compile(r"\bas\s+an?\s*(?=[,.;:]|\s*$)", re.IGNORECASE)
_SENTENCE_START_RE = re.compile(r"[.!?]\s+([a-z])")


# ---------------------------------------------------------------------------
# Rule helpers.
# ---------------------------------------------------------------------------


def _strip_dashes(text: str) -> str:
    """Rewrite em/en-dashes (with surrounding whitespace) to ``", "``."""
    if not text:
        return text
    return _DASH_RE.sub(", ", text)


def _strip_hedges(text: str) -> str:
    """Remove hedge vocabulary; tidy whitespace and capitalisation."""
    result = text
    for pattern in _HEDGE_PATTERNS:
        result = pattern.sub("", result)
    result = _MULTI_SPACE_RE.sub(" ", result)
    result = _SPACE_BEFORE_PUNCT_RE.sub(r"\1", result)
    result = _recapitalise_sentence_starts(result)
    return result.strip()


def _strip_quotes(text: str) -> str:
    """Rewrite smart/curly quotes to ASCII ``"``/``'``."""
    result = text
    for smart, ascii_equiv in _SMART_QUOTES.items():
        result = result.replace(smart, ascii_equiv)
    return result


def _strip_hyphens(text: str) -> str:
    """Space out lowercase-lowercase hyphens (``fork-lift`` → ``fork lift``).

    Proper names (``Mary-Jane``) and alphanumeric tokens (``123-A``)
    are preserved because at least one side is not lowercase ASCII.
    """
    return _LOWER_HYPHEN_RE.sub(r"\1 \2", text)


def _apply_dignified_substitutions(text: str) -> str:
    """Filter loaded labels; tidy any orphaned ``as an`` fragment."""
    result = text
    for pattern in _DIGNITY_FILTERS:
        result = pattern.sub("", result)
    result = _ORPHAN_AS_AN_RE.sub("", result)
    result = _MULTI_SPACE_RE.sub(" ", result)
    result = _SPACE_BEFORE_PUNCT_RE.sub(r"\1", result)
    return result.strip()


def _recapitalise_sentence_starts(text: str) -> str:
    """Capitalise the first alpha char and any after a sentence-ender."""
    if not text:
        return text
    chars = list(text)
    for idx, ch in enumerate(chars):
        if ch.isalpha():
            chars[idx] = ch.upper()
            break
    for match in _SENTENCE_START_RE.finditer(text):
        pos = match.start(1)
        chars[pos] = chars[pos].upper()
    return "".join(chars)


# ---------------------------------------------------------------------------
# Public API — single entry point.
# ---------------------------------------------------------------------------


def apply_worker_voice(text: str) -> str:
    """Run the full worker-voice pipeline on ``text``.

    Order: quotes → dignity filter → dashes → hyphens → hedges.
    Quotes first so later rules see a canonical character set; dignity
    before hyphens so ``ex-offender`` matches as one token. The
    pipeline is idempotent on its own output. It does **not**
    lowercase and does **not** inject vocabulary.
    """
    if not text:
        return text
    result = _strip_quotes(text)
    result = _apply_dignified_substitutions(result)
    result = _strip_dashes(result)
    result = _strip_hyphens(result)
    result = _strip_hedges(result)
    return result


# ---------------------------------------------------------------------------
# Flesch-Kincaid — pure Python, no new deps.
# ---------------------------------------------------------------------------


def _count_syllables(word: str) -> int:
    """Count syllables via vowel-group heuristic; silent trailing ``e``."""
    lowered = word.lower()
    count = len(_VOWEL_GROUP_RE.findall(lowered))
    if lowered.endswith("e") and count > 1:
        count -= 1
    return max(1, count)


def flesch_kincaid_grade(text: str) -> float:
    """Return the Flesch-Kincaid grade level of ``text``.

    ``FKG = 0.39 * (words/sentences) + 11.8 * (syllables/words) - 15.59``

    Zero-length or unpunctuated inputs clamp sentence/word counts to
    at least 1 so the formula never divides by zero.
    """
    sentences = max(1, len(_SENTENCE_END_RE.findall(text)))
    words = _WORD_RE.findall(text)
    n_words = max(1, len(words))
    syllables = sum(_count_syllables(w) for w in words)
    return (
        0.39 * (n_words / sentences)
        + 11.8 * (syllables / n_words)
        - 15.59
    )

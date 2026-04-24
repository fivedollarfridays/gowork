"""Job-description keyword extraction for the resume generator (T12.15).

Ported from ``ops:lib/resume_keywords.py``. Tokeniser + stopword list
are intentionally minimal — this is the scoring input for
:func:`app.modules.documents.resume_ranking.rank_projects`, not a
full NLP pipeline. If the ranking stays sharp-enough on keyword
frequency, richer extraction (bigrams, TF-IDF) can ship later
without changing the ranking contract.

Public API
----------
:func:`extract_keywords`
    Deduped, lowercase list of tokens mined from a JD, in
    first-occurrence order.
"""

from __future__ import annotations

import re

__all__ = ["extract_keywords"]


# Shared with the ops port; expanded with worker-relevant fillers
# ("our", "benefits", "company"). Kept small to avoid over-filtering
# low-frequency JD terms.
_STOPWORDS: frozenset[str] = frozenset(
    {
        "the", "and", "for", "with", "are", "looking", "we", "a", "an",
        "to", "of", "in", "on", "at", "is", "be", "bonus", "experience",
        "plus", "also", "need", "want", "our", "you", "your", "this",
        "that", "role", "team", "must", "have", "or", "as", "by", "about",
        "it", "its", "can", "will", "who", "what", "any", "all", "from",
        "but", "not", "do", "does", "has", "had", "was", "were", "been",
        "fluent", "expert", "senior", "junior",
    }
)

_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9+#.\-]*")


def extract_keywords(jd_text: str | None) -> list[str]:
    """Return a deduped, lowercase list of JD keywords.

    Normalisation rules, in order:
    1. Tokenise with :data:`_TOKEN_RE` (letters, digits, ``+``, ``#``,
       ``.`` and ``-`` allowed inside tokens so ``c++`` and
       ``node.js`` survive).
    2. Lowercase each token; strip trailing punctuation.
    3. Drop tokens shorter than 2 chars or in :data:`_STOPWORDS`.
    4. Dedupe with a ``seen`` set while preserving first-occurrence
       order.
    """
    if not jd_text:
        return []
    tokens = _TOKEN_RE.findall(jd_text)
    seen: set[str] = set()
    out: list[str] = []
    for token in tokens:
        normalised = token.lower().rstrip(".,;:")
        if len(normalised) < 2:
            continue
        if normalised in _STOPWORDS:
            continue
        if normalised in seen:
            continue
        seen.add(normalised)
        out.append(normalised)
    return out

"""Helpers backing ``POST /api/employers/claim`` (T24.3).

Lives next to :mod:`app.routes.employers` so the listing-claim
issuance route can stay inside the per-file size + function-count
budgets. Hosts:

* The company-name ↔ email-domain fuzzy match heuristic
  (:func:`company_matches_domain`) used to decide whether a freshly-
  minted employer row stays ``pending`` or is flagged ``admin_review``.
* Token-extraction primitives (:func:`first_significant_company_token`)
  shared by the heuristic — broken out for unit-test friendliness.

NOT a public surface — every helper here is consumed only by
:mod:`app.routes.employers`. Kept in ``app.routes`` rather than
``app.core`` because the heuristic is a *route-policy* decision (which
tier the verify path will land in), not a query-layer concern.
"""

from __future__ import annotations

import string


_MIN_SIGNIFICANT_TOKEN_LEN = 4

#: Generic noise tokens stripped from a company name before deriving
#: the significant first word. Conservative — overlap is preferred over
#: false-rejection because admin_review is a reversible outcome.
_COMPANY_NOISE_WORDS: frozenset[str] = frozenset(
    {
        "inc", "incorporated", "llc", "ltd", "limited", "corp",
        "corporation", "co", "company", "the", "and", "of",
        "industries", "group", "holdings", "services", "solutions",
        "hiring", "careers", "jobs",
    }
)


def normalize_company_word(word: str) -> str:
    """Lowercase + drop punctuation; empty if word is pure noise."""
    cleaned = "".join(ch for ch in word if ch not in string.punctuation)
    return cleaned.lower()


def first_significant_company_token(company: str) -> str | None:
    """Return the first non-noise token of *company*, or None.

    ``ACME Hiring Inc`` → ``acme``; ``The Goodwill Industries`` →
    ``goodwill``; ``LLC`` (pure noise) → None.
    """
    for raw in company.split():
        word = normalize_company_word(raw)
        if not word or word in _COMPANY_NOISE_WORDS:
            continue
        return word
    return None


def company_matches_domain(company: str | None, domain: str) -> bool:
    """Return True if *company*'s first significant word overlaps *domain*.

    Heuristic: take the first non-noise word of *company* (lowercased,
    punctuation-stripped), take the leading label of *domain*
    (everything before the first ``.``), and report a match iff one is
    a prefix of the other AND the shorter side is at least
    :data:`_MIN_SIGNIFICANT_TOKEN_LEN` chars long. None / empty company
    is conservatively treated as no match — the verify step routes
    such listings into admin_review where a human can adjudicate.
    """
    if not company:
        return False
    company_token = first_significant_company_token(company)
    if not company_token:
        return False
    domain_label = domain.lower().split(".", 1)[0]
    if not domain_label:
        return False
    short, long_ = sorted([company_token, domain_label], key=len)
    if len(short) < _MIN_SIGNIFICANT_TOKEN_LEN:
        return False
    return long_.startswith(short)


__all__ = [
    "company_matches_domain",
    "first_significant_company_token",
    "normalize_company_word",
]

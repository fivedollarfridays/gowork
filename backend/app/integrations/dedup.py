"""Fuzzy deduplication for job listings across multiple sources."""

import re

_COMPANY_SUFFIXES = re.compile(
    r"\s*\b(?:Corporation|Inc\.?|LLC|Corp\.?|Company|Co\.?|Ltd\.?|L\.?P\.?)\s*\.?\s*",
    re.IGNORECASE,
)
_TITLE_LOCATION = re.compile(
    r"\s*[-–—]\s*[A-Z][a-z]+.*$"  # " - Montgomery, AL" etc.
)
_TITLE_PARENS = re.compile(r"\s*\(.*\)\s*$")  # " (Montgomery)" etc.
_SIMILARITY_THRESHOLD = 0.85


def normalize_company(name: str | None) -> str:
    """Lowercase, strip suffixes like Inc., LLC, Corp."""
    if not name:
        return ""
    cleaned = _COMPANY_SUFFIXES.sub("", name)
    return cleaned.strip().lower()


def normalize_title(title: str | None) -> str:
    """Lowercase, strip trailing location info."""
    if not title:
        return ""
    cleaned = _TITLE_LOCATION.sub("", title)
    cleaned = _TITLE_PARENS.sub("", cleaned)
    return cleaned.strip().lower()


def similarity_score(a: str, b: str) -> float:
    """Token-overlap ratio between two strings. Returns 0.0–1.0."""
    tokens_a = set(a.lower().split())
    tokens_b = set(b.lower().split())
    if not tokens_a or not tokens_b:
        return 0.0
    overlap = len(tokens_a & tokens_b)
    total = max(len(tokens_a), len(tokens_b))
    return overlap / total


def _data_richness(listing: dict) -> int:
    """Score how much data a listing has (more = better for merge)."""
    score = 0
    for field in ("description", "url", "location", "company"):
        if listing.get(field):
            score += 1
    if listing.get("fair_chance"):
        score += 1
    return score


def _merge_pair(a: dict, b: dict) -> dict:
    """Merge two duplicate listings, preferring the one with more data."""
    if _data_richness(b) > _data_richness(a):
        winner, loser = b, a
    else:
        winner, loser = a, b

    merged = {**winner}
    # Fill in missing fields from loser
    for key in ("description", "url", "location", "company"):
        if not merged.get(key) and loser.get(key):
            merged[key] = loser[key]
    # Preserve fair_chance if either has it
    if loser.get("fair_chance"):
        merged["fair_chance"] = 1
    return merged


def deduplicate_listings(listings: list[dict]) -> list[dict]:
    """Deduplicate listings by fuzzy matching on (company, title).

    Returns a new list with duplicates merged. Preserves order of first seen.
    """
    if not listings:
        return []

    groups: list[dict] = []
    group_keys: list[tuple[str, str]] = []  # (norm_company, norm_title)

    for listing in listings:
        norm_co = normalize_company(listing.get("company"))
        norm_title = normalize_title(listing.get("title"))

        matched = False
        for i, (existing_co, existing_title) in enumerate(group_keys):
            co_match = (norm_co == existing_co) if (norm_co and existing_co) else False
            title_sim = similarity_score(norm_title, existing_title)
            if co_match and title_sim >= _SIMILARITY_THRESHOLD:
                groups[i] = _merge_pair(groups[i], listing)
                matched = True
                break

        if not matched:
            groups.append(listing)
            group_keys.append((norm_co, norm_title))

    return groups

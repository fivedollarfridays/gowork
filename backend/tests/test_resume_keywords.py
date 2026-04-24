"""Tests for JD keyword extraction (T12.15).

Ported from ops:lib/resume_keywords.py. Coverage:
- a standard JD string yields a non-empty keyword list,
- stopwords ("the", "and" …) are filtered,
- casing is normalised so "Python" and "python" collapse to a single
  token.
"""

from __future__ import annotations

from app.modules.documents.resume_keywords import extract_keywords


def test_extract_keywords_from_jd() -> None:
    """A typical JD sentence produces ranked lowercase tokens."""
    jd = "We are looking for a Python engineer with FastAPI and SQL experience"
    keywords = extract_keywords(jd)
    assert "python" in keywords
    assert "fastapi" in keywords
    assert "sql" in keywords
    assert "engineer" in keywords


def test_stopwords_filtered() -> None:
    """Common stopwords are never emitted."""
    jd = "We are looking for a worker with experience on the team"
    keywords = extract_keywords(jd)
    for bad in ("the", "and", "for", "we", "are", "a"):
        assert bad not in keywords


def test_case_normalized() -> None:
    """``Python`` and ``python`` collapse to one lowercase token."""
    jd = "Python python PYTHON"
    keywords = extract_keywords(jd)
    # Only one copy survives the seen-set dedupe.
    assert keywords.count("python") == 1


def test_empty_input_returns_empty_list() -> None:
    """Empty / falsy input yields an empty list — no crash."""
    assert extract_keywords("") == []
    assert extract_keywords(None) == []  # type: ignore[arg-type]


def test_preserves_first_occurrence_order() -> None:
    """Dedupe keeps the first-seen order of distinct tokens."""
    jd = "forklift warehouse forklift receiving"
    keywords = extract_keywords(jd)
    assert keywords.index("forklift") < keywords.index("warehouse")
    assert keywords.index("warehouse") < keywords.index("receiving")

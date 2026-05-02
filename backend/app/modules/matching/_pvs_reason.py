"""Match-reason rendering for PVS-ranked jobs.

Extracted from ``pvs_scorer`` to keep that module under the
project's per-file line / function limits. Pure text in,
text out — no I/O.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.modules.matching.relevance_scorer import matched_signal_summary
from app.modules.matching.salary_parser import SalaryInfo


def _industry_phrase(
    job: dict, target_industries: Sequence[str], searchable: str,
) -> str | None:
    """Phrase about target-industry match, or None."""
    if not job.get("industry_match"):
        return None
    if target_industries:
        matched = next(
            (i for i in target_industries if i.lower() in searchable), None,
        )
        return (
            f"Matches your target: {matched}" if matched
            else "Matches your target industry"
        )
    return "Matches your target industry"


def _keyword_phrase(
    resume_keywords: Sequence[str], searchable: str,
) -> str | None:
    """Phrase about a resume-keyword hit, or None."""
    matched = next(
        (kw for kw in resume_keywords if kw.lower() in searchable), None,
    )
    return f"Matches your {matched} experience" if matched else None


def build_pvs_reason(
    job: dict, salary: SalaryInfo | None,
    target_industries: Sequence[str] = (),
    resume_keywords: Sequence[str] = (),
    resume_signals: Sequence[str] = (),
) -> str:
    """Generate a match reason for a PVS-ranked job.

    Priority: resume signals > target industry > resume keyword >
    pay band > generic fallback.
    """
    parts: list[str] = []
    searchable = (
        f"{job.get('title', '')} {job.get('description', '')}".lower()
    )
    if resume_signals:
        summary = matched_signal_summary(resume_signals)
        if summary:
            parts.append(f"Matches your {summary}")
    industry = _industry_phrase(job, target_industries, searchable)
    if industry and (industry not in parts):
        parts.append(industry)
    if resume_keywords and not resume_signals:
        kw = _keyword_phrase(resume_keywords, searchable)
        if kw:
            parts.append(kw)
    if salary:
        parts.append(f"Pays ${salary.hourly_rate:.2f}/hr")
    if not parts:
        parts.append("Entry-level opportunity")
    return "; ".join(parts)

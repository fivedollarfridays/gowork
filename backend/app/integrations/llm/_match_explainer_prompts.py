"""Prompt assembly + deterministic fallback for match_explainer.

Extracted to keep match_explainer.py under the 150-line warning limit.
"""

from __future__ import annotations

SYSTEM_PROMPT = (
    "You are a workforce navigator for Fort Worth, TX residents who face "
    "real barriers to employment. Your job is to explain — in plain English, "
    "warmly, no jargon — why a specific job is a match for a specific person. "
    "You MUST ground your explanation in the score breakdown and any "
    "resources cited. Two paragraphs maximum. Do NOT invent facts. Do NOT "
    "speculate about wages, hours, or employer policies that weren't in the "
    "input. Address the resident directly ('you', 'your')."
)


def job_signature(job: dict) -> str:
    """Stable signature for cache key — title + company + url."""
    return f"{job.get('title','')}|{job.get('company','')}|{job.get('url','')}"


def _format_breakdown(breakdown: dict | None) -> str:
    """Render score breakdown as a compact bullet list."""
    if not breakdown:
        return "(no detailed breakdown available)"
    parts: list[str] = []
    for key in ("skills", "title_family", "industry", "years",
                "education", "certifications"):
        if key in breakdown:
            parts.append(f"- {key}: {breakdown[key]:.2f}")
    aligned = breakdown.get("industry_aligned")
    if aligned is not None:
        parts.append(f"- industry_aligned: {aligned}")
    return "\n".join(parts) if parts else "(empty breakdown)"


def _format_docs(docs: list[dict]) -> str:
    """Render top RAG docs as compact context snippets."""
    if not docs:
        return "(no relevant resources retrieved)"
    lines: list[str] = []
    for i, doc in enumerate(docs[:3], start=1):
        title = doc.get("title") or doc.get("name") or doc.get("source") or "Resource"
        text = doc.get("text") or doc.get("description") or ""
        snippet = text[:240].replace("\n", " ").strip()
        lines.append(f"{i}. {title}: {snippet}")
    return "\n".join(lines)


def build_user_prompt(
    job: dict, breakdown: dict | None, barriers: list[str], docs: list[dict],
) -> str:
    """Compose the per-call user prompt for the Haiku explainer."""
    barrier_str = ", ".join(barriers) if barriers else "(none disclosed)"
    return (
        f"Job: {job.get('title','(unknown title)')} at "
        f"{job.get('company','(unknown employer)')}\n"
        f"Location: {job.get('location','Fort Worth')}\n"
        f"Resident's barriers: {barrier_str}\n\n"
        f"Score breakdown (0..1):\n{_format_breakdown(breakdown)}\n\n"
        f"Relevant Fort Worth resources retrieved for this resident:\n"
        f"{_format_docs(docs)}\n\n"
        "Write a 2-paragraph explanation. Paragraph 1: WHY this job fits "
        "(reference the strongest score factors). Paragraph 2: ONE concrete "
        "next step that uses one of the cited resources, OR a Workforce "
        "Solutions for Tarrant County visit if no resource fits. Be honest "
        "about weaknesses if any score factor is below 0.30."
    )


def _strongest_factors(breakdown: dict | None) -> list[str]:
    if not breakdown:
        return []
    scored = [
        (k, v) for k, v in breakdown.items()
        if isinstance(v, (int, float)) and k != "industry_aligned"
    ]
    scored.sort(key=lambda kv: kv[1], reverse=True)
    return [k for k, v in scored[:2] if v >= 0.30]


def build_fallback(
    job: dict, breakdown: dict | None, barriers: list[str], docs: list[dict],
) -> str:
    """Deterministic explanation when Haiku is unavailable."""
    title = job.get("title", "this position")
    company = job.get("company", "the employer")
    strongest = _strongest_factors(breakdown)
    factor_text = (
        f"Your strongest signals are {' and '.join(strongest)}."
        if strongest
        else "We matched this position based on your overall profile."
    )
    res_name = ""
    if docs:
        res_name = docs[0].get("title") or docs[0].get("name") or ""
    next_step = (
        f"Monday morning, contact {res_name} for guidance."
        if res_name
        else "Monday morning, visit Workforce Solutions for Tarrant County "
        "at 1200 Circle Dr, Fort Worth — they can walk you through the "
        "application directly."
    )
    barrier_clause = (
        f" Given your barriers ({', '.join(barriers)}), "
        if barriers else " "
    )
    return (
        f"{title} at {company} surfaced as a match for you.{barrier_clause}"
        f"{factor_text}\n\n{next_step}"
    )

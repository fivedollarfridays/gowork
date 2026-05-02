"""Career Progression Hints — deterministic templated step-up guidance.

When a resume shows junior credentials and a job posting offers training
toward senior credentials, surface a short hint:
  "Career step up — your CNA experience fits this RN-with-training position."

This module is fully deterministic — NO LLM calls.  Pattern 12
(compositional intelligence): we map junior_family -> senior_family
edges, plus the keywords that gate the senior side.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ProgressionHint:
    """Career step-up hint for one job/resume pair."""

    junior_role: str   # e.g. "CNA"
    senior_role: str   # e.g. "RN"
    text: str          # full sentence to surface
    confidence: str    # "high" | "moderate"


# Junior family -> senior family edges + keywords that signal the senior
# side AND the training/sponsorship path.  Keys are the junior family
# (lowercased); values list candidate progressions.
_PROGRESSIONS: dict[str, list[dict]] = {
    "cna": [
        {
            "senior": "RN",
            "senior_keywords": [r"\brn\b", r"registered nurse"],
            "training_keywords": [
                r"tuition reimbursement", r"rn-to-be", r"sponsorship",
                r"training program", r"willing to train", r"will train",
                r"pathway",
            ],
            "junior_pretty": "CNA",
        },
        {
            "senior": "LVN",
            "senior_keywords": [r"\blvn\b", r"licensed vocational nurse",
                                r"\blpn\b"],
            "training_keywords": [
                r"willing to train", r"will train", r"sponsorship",
                r"training program",
            ],
            "junior_pretty": "CNA",
        },
    ],
    "warehouse": [
        {
            "senior": "warehouse supervisor",
            "senior_keywords": [r"warehouse supervisor", r"warehouse manager",
                                r"shift lead", r"operations manager"],
            "training_keywords": [
                r"will train", r"training provided", r"path to lead",
                r"path to supervisor", r"promote from within",
                r"leadership track",
            ],
            "junior_pretty": "Forklift operator / warehouse worker",
        },
    ],
    "construction": [
        {
            "senior": "foreman",
            "senior_keywords": [r"foreman", r"site supervisor",
                                r"crew leader"],
            "training_keywords": [
                r"will train", r"path to foreman", r"promote from within",
                r"leadership track",
            ],
            "junior_pretty": "Construction worker",
        },
    ],
    "customer_service": [
        {
            "senior": "team lead",
            "senior_keywords": [r"customer service supervisor",
                                r"team lead", r"call center supervisor"],
            "training_keywords": [
                r"will train", r"promote from within",
                r"leadership development",
            ],
            "junior_pretty": "Customer service rep",
        },
    ],
    "trades": [
        {
            "senior": "journeyman",
            "senior_keywords": [r"journeyman", r"licensed welder",
                                r"licensed plumber"],
            "training_keywords": [
                r"apprenticeship", r"will train", r"sponsorship",
                r"path to journeyman",
            ],
            "junior_pretty": "Apprentice / helper",
        },
    ],
}


def _job_text(job: dict) -> str:
    parts = [
        job.get("title", ""),
        job.get("company", ""),
        job.get("description", ""),
    ]
    return " ".join(p for p in parts if p).lower()


def _matches_any(text: str, patterns: list[str]) -> bool:
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)


def _matches_progression(job_text: str, prog: dict) -> bool:
    """A job matches a progression if it mentions the senior role AND the
    training pathway. Both must be present so we don't surface a spurious
    "step up" on a senior-only ad with no training language."""
    return (
        _matches_any(job_text, prog["senior_keywords"])
        and _matches_any(job_text, prog["training_keywords"])
    )


def detect_progression(
    resume_families: list[str], job: dict,
) -> ProgressionHint | None:
    """Return a hint if the resume's junior family fits a job's senior side.

    Returns None when no progression edge applies.  The matched pair is
    deterministic given the inputs.
    """
    if not resume_families or not job:
        return None
    job_text = _job_text(job)
    for family in resume_families:
        progs = _PROGRESSIONS.get(family.lower())
        if not progs:
            continue
        for prog in progs:
            if _matches_progression(job_text, prog):
                return ProgressionHint(
                    junior_role=prog["junior_pretty"],
                    senior_role=prog["senior"],
                    text=(
                        f"Career step up — your {prog['junior_pretty']} "
                        f"experience fits this {prog['senior']} position "
                        "that offers a training pathway."
                    ),
                    confidence="high",
                )
    return None


def detect_progression_for_matches(
    resume_families: list[str], matches: list,
) -> dict[int, ProgressionHint]:
    """Return ``{match_index: ProgressionHint}`` for every match with a hint.

    Tolerates dict-shape and Pydantic-model-shape matches.
    """
    out: dict[int, ProgressionHint] = {}
    for i, match in enumerate(matches):
        as_dict = match if isinstance(match, dict) else _match_to_dict(match)
        hint = detect_progression(resume_families, as_dict)
        if hint:
            out[i] = hint
    return out


def _match_to_dict(match) -> dict:
    """Best-effort projection of a Pydantic match -> dict for keyword scanning."""
    return {
        "title": getattr(match, "title", "") or "",
        "company": getattr(match, "company", "") or "",
        "description": getattr(match, "match_reason", "") or "",
    }

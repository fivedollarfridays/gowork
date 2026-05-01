"""Per-factor scoring helpers for resume<->job matching.

Extracted from :mod:`relevance_scorer` to keep that module under the
project's 15-function ceiling.  All functions here are pure: they
take a ResumeProfile + job dict and return (score, signals).
"""

from __future__ import annotations

import re

from app.modules.matching.job_keywords import INDUSTRY_KEYWORDS
from app.modules.matching.relevance_taxonomy import (
    EDU_LEVELS,
    TITLE_FAMILY,
)


def job_text(job: dict) -> str:
    """Concatenate the job's searchable fields, lowercased."""
    return (
        f"{job.get('title', '')} {job.get('company', '')} "
        f"{job.get('description', '')}"
    ).lower()


def job_industries(job: dict) -> list[str]:
    """Infer industry tags from a job's text fields."""
    text = job_text(job)
    industries: list[str] = []
    for industry, kws in INDUSTRY_KEYWORDS.items():
        for kw in kws:
            if re.search(rf"\b{re.escape(kw)}\b", text):
                if industry not in industries:
                    industries.append(industry)
                break
    if "industry" in job and job["industry"] and job["industry"] not in industries:
        industries.append(job["industry"])
    return industries


def job_families(job: dict) -> list[str]:
    """Infer job_family tags from job title/description."""
    text = job_text(job)
    families: list[str] = []
    for title_kw, family in TITLE_FAMILY.items():
        if title_kw in text and family not in families:
            families.append(family)
    return families


def factor_skills(skills: list[str], text: str) -> tuple[float, list[str]]:
    if not skills:
        return 0.0, []
    matched = [s for s in skills if re.search(rf"\b{re.escape(s)}\b", text)]
    if not matched:
        return 0.0, []
    coverage = min(len(matched) / 3.0, 1.0)
    return coverage, matched[:5]


def factor_family(
    profile_families: list[str], profile_industries: list[str],
    j_families: list[str], j_industries: list[str],
) -> tuple[float, list[str]]:
    if not profile_families and not profile_industries:
        return 0.0, []
    overlap = set(profile_families) & set(j_families)
    if overlap:
        return 1.0, list(overlap)
    same_industry = set(profile_industries) & set(j_industries)
    if same_industry:
        return 0.5, [f"industry:{i}" for i in same_industry]
    return 0.0, []


def factor_industry(
    profile_industries: list[str], j_industries: list[str],
) -> tuple[float, list[str]]:
    if not profile_industries or not j_industries:
        return 0.0, []
    overlap = set(profile_industries) & set(j_industries)
    if overlap:
        return 1.0, list(overlap)
    return 0.0, []


def factor_years(profile_years: int, job: dict) -> tuple[float, list[str]]:
    needed = int(job.get("min_years_experience", 0))
    if profile_years <= 0:
        return 0.4, []
    if profile_years >= needed:
        return 1.0, [f"{profile_years} yrs experience"]
    if profile_years >= max(needed - 1, 0):
        return 0.7, []
    return 0.3, []


def factor_education(profile_edu: int, job: dict) -> tuple[float, list[str]]:
    needed_label = job.get("education_level", "high_school")
    needed = EDU_LEVELS.get(str(needed_label).lower(), 1)
    if profile_edu <= 0:
        return 0.5, []
    if profile_edu >= needed:
        return 1.0, []
    return 0.4, []


def factor_certs(certs: list[str], text: str) -> tuple[float, list[str]]:
    if not certs:
        return 0.0, []
    matched = [c for c in certs
               if re.search(rf"\b{re.escape(c)}\b", text, re.IGNORECASE)]
    if not matched:
        return 0.0, []
    return min(len(matched) / 2.0, 1.0), matched

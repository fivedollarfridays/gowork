"""Resume <-> job semantic relevance scoring.

This is the missing factor that produced "0.363 for everyone" before.
We project both the resume and the job to a small set of signals
(skills, industries, certifications, experience, title family) and
return a 0..1 score with the matched signals named.

Static taxonomies live in :mod:`relevance_taxonomy`; per-factor
scoring helpers live in :mod:`relevance_factors`.  This module owns
ResumeProfile + the public API: build_resume_profile and
score_resume_match.
"""

from __future__ import annotations

import re
from typing import Sequence

from pydantic import BaseModel, Field

from app.modules.matching.job_keywords import INDUSTRY_KEYWORDS
from app.modules.matching.relevance_factors import (
    factor_certs,
    factor_education,
    factor_family,
    factor_industry,
    factor_skills,
    factor_years,
    job_families,
    job_industries,
    job_text,
)
from app.modules.matching.relevance_taxonomy import (
    CERTS,
    EDU_LEVELS,
    FAMILY_INDUSTRY,
    TITLE_FAMILY,
    YEARS_PATTERNS,
)

# Score weights inside score_resume_match.  These sum to 1.0:
#   skills (0.35) + family (0.25) + industry (0.20) + years (0.08)
#   + education (0.07) + cert overlap (0.05)
# Stage-2 retune: title-family weight up (was 0.20), industry weight up
# (was 0.15), years weight down (was 0.10).  Rewards true industry +
# title alignment far above incidental experience overlap.
_W_SKILLS = 0.35
_W_FAMILY = 0.25
_W_INDUSTRY = 0.20
_W_YEARS = 0.08
_W_EDU = 0.07
_W_CERT = 0.05

# Multiplier applied to the final score when the resume's inferred
# industries do not overlap the job's inferred industries.  Wrong-
# industry jobs can still surface, but they will never tie with
# right-industry jobs of comparable signal strength.
INDUSTRY_MISMATCH_MULTIPLIER = 0.55


class ResumeProfile(BaseModel):
    """Structured projection of a resume into matchable signals."""

    skills: list[str] = Field(default_factory=list)
    industries: list[str] = Field(default_factory=list)
    job_titles_held: list[str] = Field(default_factory=list)
    job_families: list[str] = Field(default_factory=list)
    years_experience: int = 0
    certifications: list[str] = Field(default_factory=list)
    education_level: int = 0  # 0=unknown, 1=HS, 2=AA, 3=BA, 4=MA, 5=PhD/MD


def _extract_skills(text: str) -> list[str]:
    """Match resume text against the INDUSTRY_KEYWORDS skill set."""
    if not text.strip():
        return []
    lower = text.lower()
    found: list[str] = []
    for keywords in INDUSTRY_KEYWORDS.values():
        for kw in keywords:
            if re.search(rf"\b{re.escape(kw)}\b", lower) and kw not in found:
                found.append(kw)
    return found


def _extract_certifications(text: str) -> list[str]:
    """Detect certifications by trying every alias regex."""
    if not text.strip():
        return []
    found: list[str] = []
    for canonical, patterns in CERTS.items():
        for p in patterns:
            if re.search(p, text, re.IGNORECASE):
                if canonical not in found:
                    found.append(canonical)
                break
    return found


def _extract_titles_and_families(text: str) -> tuple[list[str], list[str]]:
    """Match resume text against the title taxonomy with word boundaries.

    Substring matching used to leak short tokens (``rn``, ``cna``) inside
    unrelated words (``leaRN``, ``CNAvy``).  Stage-2 fix anchors each
    keyword with ``\\b`` on both sides.
    """
    if not text.strip():
        return [], []
    lower = text.lower()
    titles: list[str] = []
    families: list[str] = []
    for title_kw, family in TITLE_FAMILY.items():
        pattern = rf"\b{re.escape(title_kw.strip())}\b"
        if re.search(pattern, lower):
            if title_kw not in titles:
                titles.append(title_kw)
            if family not in families:
                families.append(family)
    return titles, families


def _infer_industries(skills: list[str], families: list[str]) -> list[str]:
    """Reverse-map skills -> industries; merge with family-derived industries."""
    industries: list[str] = []
    skill_set = set(skills)
    for industry, kws in INDUSTRY_KEYWORDS.items():
        if skill_set & kws and industry not in industries:
            industries.append(industry)
    for fam in families:
        ind = FAMILY_INDUSTRY.get(fam)
        if ind and ind not in industries:
            industries.append(ind)
    return industries


def _extract_years_experience(text: str) -> int:
    """Return the largest "N years" mention found."""
    if not text.strip():
        return 0
    best = 0
    for pattern in YEARS_PATTERNS:
        for match in pattern.finditer(text):
            try:
                value = int(match.group(1))
                if 0 < value <= 50 and value > best:
                    best = value
            except ValueError:
                continue
    if best == 0 and re.search(r"\bdecade\b", text, re.IGNORECASE):
        return 10
    return best


def _extract_education_level(text: str) -> int:
    """Return education level 0-5 from common degree/diploma phrases."""
    if not text.strip():
        return 0
    lower = text.lower()
    best = 0
    for keyword, level in EDU_LEVELS.items():
        token = keyword.replace("_degree", "")
        if re.search(rf"\b{re.escape(token)}\b", lower):
            best = max(best, level)
    return best


def build_resume_profile(text: str) -> ResumeProfile:
    """Project raw resume text into a ResumeProfile."""
    if not text or not text.strip():
        return ResumeProfile()
    skills = _extract_skills(text)
    titles, families = _extract_titles_and_families(text)
    certs = _extract_certifications(text)
    industries = _infer_industries(skills, families)
    years = _extract_years_experience(text)
    edu = _extract_education_level(text)
    return ResumeProfile(
        skills=skills,
        industries=industries,
        job_titles_held=titles,
        job_families=families,
        certifications=certs,
        years_experience=years,
        education_level=edu,
    )


def score_resume_match(
    job: dict, profile: ResumeProfile,
) -> tuple[float, list[str]]:
    """Compute resume<->job semantic match (0..1) plus matched signals.

    Returns (score, signals) where signals are short human-readable
    strings naming what matched (used in match_reason text).
    """
    if not profile.skills and not profile.industries and not profile.job_families:
        return 0.30, []

    text = job_text(job)
    j_industries = job_industries(job)
    j_families = job_families(job)

    industry_aligned = bool(set(profile.industries) & set(j_industries))

    skills, skill_sigs = factor_skills(profile.skills, text)
    family, family_sigs = factor_family(
        profile.job_families, profile.industries, j_families, j_industries,
    )
    industry, industry_sigs = factor_industry(profile.industries, j_industries)
    years, years_sigs = factor_years(
        profile.years_experience, job, industry_aligned=industry_aligned,
    )
    edu, _ = factor_education(profile.education_level, job)
    cert, cert_sigs = factor_certs(profile.certifications, text)

    score = (
        _W_SKILLS * skills
        + _W_FAMILY * family
        + _W_INDUSTRY * industry
        + _W_YEARS * years
        + _W_EDU * edu
        + _W_CERT * cert
    )
    # Stage-2 industry-mismatch dampener: kept resume-aware (only
    # applied when the user actually has signal; an empty-industry
    # resume hits the early-return above with score=0.30).
    if profile.industries and j_industries and not industry_aligned:
        score *= INDUSTRY_MISMATCH_MULTIPLIER

    signals = skill_sigs + family_sigs + industry_sigs + years_sigs + cert_sigs
    return round(min(max(score, 0.0), 1.0), 3), signals


def resume_keywords_for_context(profile: ResumeProfile) -> list[str]:
    """Flatten a ResumeProfile into the resume_keywords list ScoringContext expects."""
    out: list[str] = []
    seen: set[str] = set()
    for source in (profile.skills, profile.certifications, profile.job_titles_held):
        for item in source:
            key = item.lower()
            if key not in seen:
                seen.add(key)
                out.append(item)
    return out


def matched_signal_summary(signals: Sequence[str]) -> str:
    """Render matched signals as a short, human-readable phrase."""
    if not signals:
        return ""
    deduped: list[str] = []
    for sig in signals:
        if sig not in deduped:
            deduped.append(sig)
    return ", ".join(deduped[:3])

"""Job Readiness Score engine — mirrors Credit Readiness Score pattern."""

from __future__ import annotations

from app.modules.matching.job_readiness_pathway import build_pathway
from app.modules.matching.job_readiness_types import (
    JobReadinessResult,
    ReadinessBand,
    ReadinessFactor,
)
from app.modules.matching.resume_parser import ParsedResume
from app.modules.matching.types import ScoredJobMatch, UserProfile

# Factor weights (sum to 1.0)
W_SKILLS = 0.30
W_INDUSTRY = 0.25
W_BARRIERS = 0.20
W_EXPERIENCE = 0.15
W_CREDIT = 0.10

_BAND_SUMMARIES = {
    ReadinessBand.NOT_READY: (
        "Your profile needs some work before you're ready for most jobs. "
        "Focus on the pathway steps below to improve your readiness."
    ),
    ReadinessBand.DEVELOPING: (
        "You're making progress! A few more steps will significantly "
        "improve your job readiness."
    ),
    ReadinessBand.READY: (
        "You're ready for many jobs in your target industries. "
        "Follow the pathway to maximize your options."
    ),
    ReadinessBand.STRONG: (
        "You have a strong profile for employment. "
        "You're well-positioned for the jobs in your plan."
    ),
}

# Factor definitions: (name, weight, detail)
_FACTOR_DEFS = [
    ("Skills Match", W_SKILLS, "Resume skills vs job requirements"),
    ("Industry Alignment", W_INDUSTRY, "Target industries vs available jobs"),
    ("Barrier Resolution", W_BARRIERS, "Employment barriers remaining"),
    ("Work Experience", W_EXPERIENCE, "Resume quality and certifications"),
    ("Credit Readiness", W_CREDIT, "Credit status for employment"),
]


def _determine_band(score: int) -> ReadinessBand:
    """Map 0-100 score to readiness band."""
    if score >= 80:
        return ReadinessBand.STRONG
    if score >= 60:
        return ReadinessBand.READY
    if score >= 40:
        return ReadinessBand.DEVELOPING
    return ReadinessBand.NOT_READY


def _score_skills_match(
    resume: ParsedResume | None, jobs: list[ScoredJobMatch],
) -> int:
    """Score 0-100: how well user's skills match available jobs."""
    if not jobs:
        return 20
    if resume and resume.skills:
        base = min(len(resume.skills) * 15, 70)
        return min(base + min(len(jobs) * 10, 30), 100)
    return min(len(jobs) * 20, 60)


def _score_industry_alignment(
    profile: UserProfile, jobs: list[ScoredJobMatch],
) -> int:
    """Score 0-100: target industries vs available jobs."""
    if not jobs:
        return 20
    if not profile.target_industries:
        return 30
    base = min(len(profile.target_industries) * 20, 60)
    return min(base + min(len(jobs) * 10, 40), 100)


def _score_barrier_resolution(profile: UserProfile) -> int:
    """Score 0-100: fewer barriers = higher score."""
    if profile.barrier_count == 0:
        return 100
    base = {"low": 75, "medium": 50, "high": 25}.get(
        profile.barrier_severity.value, 50,
    )
    return max(base - profile.barrier_count * 8, 10)


def _score_work_experience(
    profile: UserProfile, resume: ParsedResume | None,
) -> int:
    """Score 0-100: resume quality + certifications + work history."""
    if resume:
        score = 0
        if resume.word_count >= 200:
            score += 30
        elif resume.word_count >= 100:
            score += 20
        elif resume.word_count > 0:
            score += 10
        score += min(len(resume.certifications) * 15, 30)
        score += min(len(resume.experience_keywords) * 10, 20)
        score += min(len(resume.skills) * 3, 20)
        return min(score, 100)

    wh_len = len(profile.work_history.strip())
    if wh_len > 200:
        return 40
    if wh_len > 50:
        return 25
    return 10 if wh_len > 0 else 0


def _score_credit_readiness(
    profile: UserProfile, credit_result: dict | None,
) -> int:
    """Score 0-100: credit readiness (100 if no credit barrier)."""
    if not profile.needs_credit_assessment:
        return 100
    if credit_result and isinstance(credit_result, dict):
        readiness = credit_result.get("readiness", {})
        if isinstance(readiness, dict):
            val = readiness.get("score")
            if isinstance(val, (int, float)):
                return max(0, min(int(val), 100))
    return 20


# Re-export for test imports
_build_pathway = build_pathway


def assess_job_readiness(
    profile: UserProfile,
    parsed_resume: ParsedResume | None,
    job_matches: list[ScoredJobMatch],
    credit_result: dict | None,
) -> JobReadinessResult:
    """Assess job readiness and return structured result."""
    scores = [
        _score_skills_match(parsed_resume, job_matches),
        _score_industry_alignment(profile, job_matches),
        _score_barrier_resolution(profile),
        _score_work_experience(profile, parsed_resume),
        _score_credit_readiness(profile, credit_result),
    ]
    factors = [
        ReadinessFactor(name=name, weight=weight, score=s, detail=detail)
        for (name, weight, detail), s in zip(_FACTOR_DEFS, scores)
    ]

    weighted = sum(f.weight * f.score for f in factors)
    overall = max(0, min(int(round(weighted)), 100))
    band = _determine_band(overall)
    pathway = build_pathway(profile, factors)

    return JobReadinessResult(
        overall_score=overall,
        readiness_band=band,
        factors=factors,
        pathway=pathway,
        estimated_days_to_ready=sum(s.timeline_days for s in pathway),
        summary=_BAND_SUMMARIES[band],
    )

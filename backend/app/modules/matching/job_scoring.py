"""Job scoring: weighted relevance formula and rank/bucket logic."""

from app.modules.matching.job_keywords import SKILLS_STOP_WORDS
from app.modules.matching.types import MatchBucket, ScoredJobMatch

# Scoring weights
W_INDUSTRY = 0.30
W_SKILLS = 0.25
W_SCHEDULE = 0.15
W_TRANSIT = 0.15
W_BARRIERS = 0.15


def job_search_text(job: dict) -> str:
    """Concatenate searchable fields from a job dict."""
    return f"{job['title']} {job.get('company', '')} {job.get('description', '')}".lower()


def _extract_history_tokens(work_history: str) -> set[str]:
    """Extract meaningful tokens from work history text."""
    return {w for w in work_history.lower().split() if w not in SKILLS_STOP_WORDS and len(w) > 2}


def _score_industry(job: dict) -> float:
    """30% weight: 1.0 if industry match, 0.1 if mismatch."""
    return 1.0 if job.get("industry_match") else 0.1


def _score_skills(job: dict, work_history: str) -> float:
    """25% weight: token overlap between work_history and job text."""
    if not work_history:
        return 0.3
    history_tokens = _extract_history_tokens(work_history)
    if not history_tokens:
        return 0.3
    job_tokens = {w for w in job_search_text(job).split() if len(w) > 2}
    overlap = len(history_tokens & job_tokens)
    return min(overlap / max(len(history_tokens), 1), 1.0)


def _score_schedule(job: dict) -> float:
    """15% weight: 1.0 no conflict, 0.0 conflict."""
    return 0.0 if job.get("schedule_conflict") else 1.0


def _score_transit(job: dict, transit_dependent: bool) -> float:
    """15% weight: score based on accessibility, walk distance, and transfers."""
    if not transit_dependent:
        return 1.0
    if not job.get("transit_accessible"):
        return 0.0

    info = job.get("transit_info")
    if info is None:
        # Legacy path: keyword-only detection
        return 0.5 if job.get("sunday_flag") else 1.0

    # Walk distance factor (closest serving route)
    walk = info.serving_routes[0].walk_miles if info.serving_routes else 1.0
    if walk <= 0.25:
        walk_score = 1.0
    elif walk <= 0.5:
        walk_score = 0.9
    elif walk <= 1.0:
        walk_score = 0.7
    else:
        walk_score = 0.4

    # Transfer penalty
    if info.transfer_count == 0:
        transfer_mult = 1.0
    elif info.transfer_count == 1:
        transfer_mult = 0.8
    else:
        transfer_mult = 0.6

    # Schedule feasibility
    has_infeasible = any(not r.feasible for r in info.serving_routes)
    schedule_mult = 0.5 if has_infeasible else 1.0

    return round(walk_score * transfer_mult * schedule_mult, 3)


def _score_barriers(job: dict) -> float:
    """15% weight: 1.0 no blockers, 0.0 credit-blocked."""
    return 0.0 if job.get("credit_blocked") else 1.0


def _build_match_reason(job: dict, industry_score: float, skills_score: float, work_history: str) -> str:
    """Generate human-readable match reason."""
    parts: list[str] = []
    if industry_score >= 1.0:
        parts.append("Matches your target industry")
    if skills_score >= 0.4 and work_history:
        history_tokens = _extract_history_tokens(work_history)
        job_text = job_search_text(job)
        matching = [t for t in history_tokens if t in job_text]
        if matching:
            parts.append(f"Matches your {matching[0].upper()} experience")
    if not parts:
        parts.append("Entry-level opportunity")
    return "; ".join(parts)


def score_job(job: dict, work_history: str, transit_dependent: bool) -> tuple[float, str]:
    """Compute weighted relevance score and match_reason string."""
    industry = _score_industry(job)
    skills = _score_skills(job, work_history)
    schedule = _score_schedule(job)
    transit = _score_transit(job, transit_dependent)
    barriers = _score_barriers(job)

    raw = (
        W_INDUSTRY * industry
        + W_SKILLS * skills
        + W_SCHEDULE * schedule
        + W_TRANSIT * transit
        + W_BARRIERS * barriers
    )
    score = max(0.0, min(1.0, raw))

    reason = _build_match_reason(job, industry, skills, work_history)
    return score, reason


def rank_and_bucket(
    jobs: list[dict], work_history: str, transit_dependent: bool,
) -> tuple[list[ScoredJobMatch], list[ScoredJobMatch], list[ScoredJobMatch]]:
    """Score all jobs, sort by score, split into strong/possible/after_repair."""
    scored: list[tuple[float, str, dict]] = []
    for job in jobs:
        s, reason = score_job(job, work_history, transit_dependent)
        scored.append((s, reason, job))

    scored.sort(key=lambda x: x[0], reverse=True)

    strong: list[ScoredJobMatch] = []
    possible: list[ScoredJobMatch] = []
    after_repair: list[ScoredJobMatch] = []

    for s, reason, job in scored:
        match = ScoredJobMatch(
            title=job["title"],
            company=job.get("company"),
            location=job.get("location"),
            url=job.get("url"),
            source=job.get("source"),
            credit_check_required=job.get("credit_check", "unknown"),
            transit_accessible=job.get("transit_accessible", False),
            relevance_score=round(s, 3),
            match_reason=reason,
            bucket=MatchBucket.POSSIBLE,
        )
        if job.get("credit_blocked"):
            if len(after_repair) < 5:
                match.bucket = MatchBucket.AFTER_REPAIR
                after_repair.append(match)
        elif s >= 0.6 and len(strong) < 5:
            match.bucket = MatchBucket.STRONG
            strong.append(match)
        elif len(possible) < 5:
            match.bucket = MatchBucket.POSSIBLE
            possible.append(match)

    return strong, possible, after_repair

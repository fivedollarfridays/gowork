"""Tests for empty-profile handling in Job Readiness scorer (S13-T72 fix).

When a session has no work history, no resume, no target industries, and no
barriers selected, the scorer was returning a confident `developing — 41/100`
band that misrepresented an unfilled assessment as a real signal. The fix
returns `None` so the frontend cleanly suppresses the Job Readiness section.
"""

from app.modules.matching.job_readiness import assess_job_readiness
from app.modules.matching.job_readiness_types import JobReadinessResult, ReadinessBand
from app.modules.matching.resume_parser import ParsedResume
from app.modules.matching.types import (
    AvailableHours,
    BarrierSeverity,
    BarrierType,
    EmploymentStatus,
    MatchBucket,
    ScoredJobMatch,
    UserProfile,
)


def _profile(**overrides) -> UserProfile:
    defaults = {
        "session_id": "sess-empty",
        "zip_code": "36104",
        "employment_status": EmploymentStatus.UNEMPLOYED,
        "barrier_count": 0,
        "primary_barriers": [],
        "barrier_severity": BarrierSeverity.LOW,
        "needs_credit_assessment": False,
        "transit_dependent": False,
        "schedule_type": AvailableHours.DAYTIME,
        "work_history": "",
        "target_industries": [],
    }
    defaults.update(overrides)
    return UserProfile(**defaults)


def _job(title: str = "Cashier") -> ScoredJobMatch:
    return ScoredJobMatch(
        title=title,
        company="Test Co",
        relevance_score=0.7,
        bucket=MatchBucket.STRONG,
    )


class TestEmptyProfileReturnsNone:
    def test_empty_profile_no_resume_no_jobs_returns_none(self):
        """Truly empty profile → suppress readiness entirely."""
        result = assess_job_readiness(_profile(), None, [], None)
        assert result is None

    def test_empty_profile_with_jobs_still_returns_none(self):
        """Even if jobs are matched, no profile data = no meaningful score."""
        result = assess_job_readiness(_profile(), None, [_job()], None)
        assert result is None

    def test_empty_profile_blank_resume_returns_none(self):
        """A resume object with zero content is also empty."""
        empty_resume = ParsedResume(
            skills=[], industries=[], certifications=[],
            experience_keywords=[], word_count=0,
        )
        result = assess_job_readiness(_profile(), empty_resume, [], None)
        assert result is None


class TestPartialProfileReturnsScore:
    def test_work_history_only_returns_real_score(self):
        """If user has work history, give them a real score."""
        profile = _profile(work_history="3 years cashier at Walmart")
        result = assess_job_readiness(profile, None, [], None)
        assert isinstance(result, JobReadinessResult)
        assert 0 <= result.overall_score <= 100

    def test_target_industries_only_returns_real_score(self):
        profile = _profile(target_industries=["retail"])
        result = assess_job_readiness(profile, None, [], None)
        assert isinstance(result, JobReadinessResult)

    def test_barriers_selected_returns_real_score(self):
        """User selected barriers — that's real signal, score them."""
        profile = _profile(
            barrier_count=1,
            primary_barriers=[BarrierType.TRANSPORTATION],
            transit_dependent=True,
        )
        result = assess_job_readiness(profile, None, [], None)
        assert isinstance(result, JobReadinessResult)


class TestFullProfileReturnsRealScore:
    def test_full_profile_returns_real_score_and_band(self):
        """Sanity: a fully-filled profile still scores normally."""
        profile = _profile(
            barrier_count=1,
            primary_barriers=[BarrierType.TRANSPORTATION],
            barrier_severity=BarrierSeverity.LOW,
            transit_dependent=True,
            work_history="5 years experience as cashier and warehouse worker",
            target_industries=["retail", "manufacturing"],
        )
        resume = ParsedResume(
            skills=["cashier", "forklift", "customer service"],
            industries=["retail"],
            certifications=["CNA"],
            experience_keywords=["cashier", "warehouse"],
            word_count=200,
        )
        result = assess_job_readiness(profile, resume, [_job()], None)
        assert isinstance(result, JobReadinessResult)
        assert result.overall_score > 0
        assert result.readiness_band in {
            ReadinessBand.NOT_READY,
            ReadinessBand.DEVELOPING,
            ReadinessBand.READY,
            ReadinessBand.STRONG,
        }

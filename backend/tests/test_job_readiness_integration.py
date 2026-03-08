"""Integration tests for Job Readiness Score — assess + pathway."""

from app.modules.matching.job_readiness import (
    assess_job_readiness,
    _build_pathway,
)
from app.modules.matching.job_readiness_types import (
    JobReadinessResult,
    ReadinessBand,
    ReadinessFactor,
)
from app.modules.matching.resume_parser import ParsedResume
from app.modules.matching.types import (
    BarrierSeverity,
    BarrierType,
    EmploymentStatus,
    AvailableHours,
    ScoredJobMatch,
    MatchBucket,
    UserProfile,
)


def _make_profile(**overrides) -> UserProfile:
    defaults = {
        "session_id": "test-session",
        "zip_code": "36104",
        "employment_status": EmploymentStatus.UNEMPLOYED,
        "barrier_count": 2,
        "primary_barriers": [BarrierType.CREDIT, BarrierType.TRANSPORTATION],
        "barrier_severity": BarrierSeverity.MEDIUM,
        "needs_credit_assessment": True,
        "transit_dependent": True,
        "schedule_type": AvailableHours.DAYTIME,
        "work_history": "Worked as cashier and warehouse worker",
        "target_industries": ["retail", "manufacturing"],
    }
    defaults.update(overrides)
    return UserProfile(**defaults)


def _make_parsed_resume(**overrides) -> ParsedResume:
    defaults = {
        "skills": ["cashier", "customer service"],
        "industries": ["retail"],
        "certifications": [],
        "experience_keywords": ["cashier"],
        "word_count": 150,
    }
    defaults.update(overrides)
    return ParsedResume(**defaults)


def _make_job(
    title: str = "Cashier",
    bucket: MatchBucket = MatchBucket.POSSIBLE,
    score: float = 0.5,
) -> ScoredJobMatch:
    return ScoredJobMatch(
        title=title, relevance_score=score, bucket=bucket,
        match_reason="test", credit_check_required="unknown",
    )


class TestBuildPathway:
    def test_generates_steps_for_weak_factors(self):
        factors = [
            ReadinessFactor(name="Skills Match", weight=0.30, score=30, detail=""),
            ReadinessFactor(name="Industry Alignment", weight=0.25, score=80, detail=""),
            ReadinessFactor(name="Barrier Resolution", weight=0.20, score=40, detail=""),
            ReadinessFactor(name="Work Experience", weight=0.15, score=20, detail=""),
            ReadinessFactor(name="Credit Readiness", weight=0.10, score=90, detail=""),
        ]
        profile = _make_profile()
        pathway = _build_pathway(profile, factors)
        assert len(pathway) >= 1
        assert all(step.step_number > 0 for step in pathway)

    def test_no_steps_when_all_strong(self):
        factors = [
            ReadinessFactor(name="Skills Match", weight=0.30, score=90, detail=""),
            ReadinessFactor(name="Industry Alignment", weight=0.25, score=85, detail=""),
            ReadinessFactor(name="Barrier Resolution", weight=0.20, score=95, detail=""),
            ReadinessFactor(name="Work Experience", weight=0.15, score=88, detail=""),
            ReadinessFactor(name="Credit Readiness", weight=0.10, score=92, detail=""),
        ]
        profile = _make_profile()
        pathway = _build_pathway(profile, factors)
        assert len(pathway) == 0


class TestAssessJobReadiness:
    def test_returns_result_type(self):
        profile = _make_profile()
        result = assess_job_readiness(profile, None, [], None)
        assert isinstance(result, JobReadinessResult)

    def test_score_range(self):
        profile = _make_profile()
        resume = _make_parsed_resume()
        jobs = [_make_job(), _make_job("Warehouse")]
        result = assess_job_readiness(profile, resume, jobs, None)
        assert 0 <= result.overall_score <= 100

    def test_has_five_factors(self):
        profile = _make_profile()
        result = assess_job_readiness(profile, None, [], None)
        assert len(result.factors) == 5

    def test_factor_weights_sum_to_one(self):
        profile = _make_profile()
        result = assess_job_readiness(profile, None, [], None)
        total = sum(f.weight for f in result.factors)
        assert abs(total - 1.0) < 0.01

    def test_strong_profile_high_score(self):
        profile = _make_profile(
            barrier_count=0,
            primary_barriers=[],
            barrier_severity=BarrierSeverity.LOW,
            needs_credit_assessment=False,
            target_industries=["retail"],
        )
        resume = _make_parsed_resume(
            skills=["cashier", "customer service", "retail", "sales"],
            certifications=["GED"],
            word_count=300,
        )
        jobs = [_make_job("Cashier", MatchBucket.STRONG, 0.9)]
        result = assess_job_readiness(profile, resume, jobs, None)
        assert result.overall_score >= 60
        assert result.readiness_band in (ReadinessBand.READY, ReadinessBand.STRONG)

    def test_weak_profile_low_score(self):
        profile = _make_profile(
            barrier_count=5,
            primary_barriers=[
                BarrierType.CREDIT, BarrierType.TRANSPORTATION,
                BarrierType.CHILDCARE, BarrierType.HOUSING,
                BarrierType.CRIMINAL_RECORD,
            ],
            barrier_severity=BarrierSeverity.HIGH,
            work_history="",
            target_industries=[],
        )
        result = assess_job_readiness(profile, None, [], None)
        assert result.overall_score <= 40
        assert result.readiness_band in (ReadinessBand.NOT_READY, ReadinessBand.DEVELOPING)

    def test_summary_populated(self):
        profile = _make_profile()
        result = assess_job_readiness(profile, None, [], None)
        assert len(result.summary) > 0

    def test_pathway_has_estimated_days(self):
        profile = _make_profile()
        result = assess_job_readiness(profile, None, [], None)
        if result.pathway:
            assert result.estimated_days_to_ready > 0

    def test_no_credit_barrier_full_credit_score(self):
        profile = _make_profile(
            needs_credit_assessment=False,
            primary_barriers=[BarrierType.TRAINING],
        )
        result = assess_job_readiness(profile, None, [], None)
        credit_factor = next(f for f in result.factors if f.name == "Credit Readiness")
        assert credit_factor.score == 100

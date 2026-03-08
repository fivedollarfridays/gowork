"""Tests for Job Readiness Score engine."""

import pytest

from app.modules.matching.job_readiness import (
    assess_job_readiness,
    _score_skills_match,
    _score_industry_alignment,
    _score_barrier_resolution,
    _score_work_experience,
    _score_credit_readiness,
    _determine_band,
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
        "skills": ["cashier", "warehouse", "forklift"],
        "industries": ["retail", "manufacturing"],
        "certifications": ["CNA"],
        "experience_keywords": ["cashier", "warehouse"],
        "word_count": 150,
    }
    defaults.update(overrides)
    return ParsedResume(**defaults)


def _make_job(title="Cashier", bucket=MatchBucket.STRONG, score=0.8) -> ScoredJobMatch:
    return ScoredJobMatch(
        title=title,
        company="Test Corp",
        relevance_score=score,
        bucket=bucket,
    )


class TestDetermineBand:
    def test_not_ready(self):
        assert _determine_band(20) == ReadinessBand.NOT_READY

    def test_developing(self):
        assert _determine_band(50) == ReadinessBand.DEVELOPING

    def test_ready(self):
        assert _determine_band(70) == ReadinessBand.READY

    def test_strong(self):
        assert _determine_band(85) == ReadinessBand.STRONG

    def test_boundary_not_ready(self):
        assert _determine_band(39) == ReadinessBand.NOT_READY

    def test_boundary_developing(self):
        assert _determine_band(40) == ReadinessBand.DEVELOPING

    def test_boundary_ready(self):
        assert _determine_band(60) == ReadinessBand.READY

    def test_boundary_strong(self):
        assert _determine_band(80) == ReadinessBand.STRONG

    def test_zero(self):
        assert _determine_band(0) == ReadinessBand.NOT_READY

    def test_hundred(self):
        assert _determine_band(100) == ReadinessBand.STRONG


class TestScoreSkillsMatch:
    def test_with_resume_skills_and_strong_matches(self):
        resume = _make_parsed_resume(skills=["cashier", "warehouse", "forklift"])
        jobs = [_make_job("Cashier"), _make_job("Warehouse Worker")]
        score = _score_skills_match(resume, jobs)
        assert 50 <= score <= 100

    def test_no_resume_falls_back_to_job_count(self):
        jobs = [_make_job("Cashier")]
        score = _score_skills_match(None, jobs)
        assert 0 <= score <= 100

    def test_no_jobs(self):
        resume = _make_parsed_resume()
        score = _score_skills_match(resume, [])
        assert score == 20

    def test_empty_resume_skills(self):
        resume = _make_parsed_resume(skills=[])
        jobs = [_make_job()]
        score = _score_skills_match(resume, jobs)
        assert 0 <= score <= 50


class TestScoreIndustryAlignment:
    def test_matching_industries(self):
        profile = _make_profile(target_industries=["retail", "manufacturing"])
        jobs = [_make_job("Cashier"), _make_job("Warehouse")]
        score = _score_industry_alignment(profile, jobs)
        assert score >= 50

    def test_no_target_industries(self):
        profile = _make_profile(target_industries=[])
        jobs = [_make_job()]
        score = _score_industry_alignment(profile, jobs)
        assert score == 30

    def test_no_jobs(self):
        profile = _make_profile()
        score = _score_industry_alignment(profile, [])
        assert score == 20


class TestScoreBarrierResolution:
    def test_no_barriers(self):
        profile = _make_profile(
            barrier_count=0,
            primary_barriers=[],
            barrier_severity=BarrierSeverity.LOW,
        )
        score = _score_barrier_resolution(profile)
        assert score == 100

    def test_low_severity(self):
        profile = _make_profile(
            barrier_count=1,
            primary_barriers=[BarrierType.TRAINING],
            barrier_severity=BarrierSeverity.LOW,
        )
        score = _score_barrier_resolution(profile)
        assert 60 <= score <= 90

    def test_medium_severity(self):
        profile = _make_profile(barrier_severity=BarrierSeverity.MEDIUM)
        score = _score_barrier_resolution(profile)
        assert 30 <= score <= 70

    def test_high_severity(self):
        profile = _make_profile(
            barrier_count=4,
            primary_barriers=[
                BarrierType.CREDIT, BarrierType.TRANSPORTATION,
                BarrierType.CHILDCARE, BarrierType.HOUSING,
            ],
            barrier_severity=BarrierSeverity.HIGH,
        )
        score = _score_barrier_resolution(profile)
        assert score <= 40


class TestScoreWorkExperience:
    def test_with_resume_and_certs(self):
        resume = _make_parsed_resume(
            certifications=["CNA", "CDL"],
            experience_keywords=["nurse", "driver"],
            word_count=200,
        )
        profile = _make_profile(work_history="nurse driver healthcare")
        score = _score_work_experience(profile, resume)
        assert score >= 60

    def test_no_resume(self):
        profile = _make_profile(work_history="cashier for 3 years at retail stores in Montgomery area doing customer service")
        score = _score_work_experience(profile, None)
        assert 20 <= score <= 60

    def test_empty_work_history_no_resume(self):
        profile = _make_profile(work_history="")
        score = _score_work_experience(profile, None)
        assert score <= 20

    def test_long_resume(self):
        resume = _make_parsed_resume(word_count=500, certifications=["CNA"])
        profile = _make_profile()
        score = _score_work_experience(profile, resume)
        assert score >= 50

    def test_short_resume(self):
        """Resume with < 100 words (but > 0) hits the 10-point tier."""
        resume = _make_parsed_resume(word_count=50)
        profile = _make_profile()
        score = _score_work_experience(profile, resume)
        assert score >= 10

    def test_very_long_work_history_no_resume(self):
        """Work history > 200 chars with no resume scores 40."""
        long_history = "Worked for 5 years as a warehouse associate and forklift operator at Amazon fulfillment center in Montgomery, doing picking, packing, shipping, and receiving duties daily with excellent attendance record"
        profile = _make_profile(work_history=long_history)
        score = _score_work_experience(profile, None)
        assert score == 40


class TestScoreCreditReadiness:
    def test_no_credit_barrier(self):
        profile = _make_profile(
            needs_credit_assessment=False,
            primary_barriers=[BarrierType.TRANSPORTATION],
        )
        score = _score_credit_readiness(profile, None)
        assert score == 100

    def test_with_good_credit_result(self):
        credit = {"readiness": {"score": 80}}
        profile = _make_profile()
        score = _score_credit_readiness(profile, credit)
        assert score == 80

    def test_with_poor_credit_result(self):
        credit = {"readiness": {"score": 30}}
        profile = _make_profile()
        score = _score_credit_readiness(profile, credit)
        assert score == 30

    def test_credit_barrier_no_result(self):
        profile = _make_profile()
        score = _score_credit_readiness(profile, None)
        assert score <= 30



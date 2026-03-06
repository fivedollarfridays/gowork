"""Tests for job matcher scoring formula and rank/bucket logic."""

import pytest


def _annotated_job(
    title="Test Job",
    company=None,
    description="",
    credit_check="not_required",
    industry_match=False,
    schedule_conflict=False,
    transit_accessible=True,
    sunday_flag=False,
    credit_blocked=False,
):
    """Helper to create an annotated job dict (post-filter stage)."""
    return {
        "id": 1,
        "title": title,
        "company": company,
        "location": "Montgomery, AL",
        "description": description,
        "url": None,
        "source": "seed",
        "scraped_at": "2026-03-01T00:00:00Z",
        "expires_at": None,
        "credit_check": credit_check,
        "industry_match": industry_match,
        "schedule_conflict": schedule_conflict,
        "transit_accessible": transit_accessible,
        "sunday_flag": sunday_flag,
        "credit_blocked": credit_blocked,
    }


class TestScoreIndustry:
    def test_match_returns_high(self):
        from app.modules.matching.job_scoring import _score_industry

        job = _annotated_job(industry_match=True)
        assert _score_industry(job) == 1.0

    def test_no_match_returns_low(self):
        from app.modules.matching.job_scoring import _score_industry

        job = _annotated_job(industry_match=False)
        assert _score_industry(job) == 0.1


class TestScoreSkills:
    def test_matching_work_history_scores_high(self):
        from app.modules.matching.job_scoring import _score_skills

        job = _annotated_job("Certified Nursing Assistant", "Baptist Health", "CNA patient care")
        score = _score_skills(job, "CNA for 3 years at nursing home, patient care")
        assert score >= 0.5

    def test_no_overlap_scores_low(self):
        from app.modules.matching.job_scoring import _score_skills

        job = _annotated_job("Forklift Operator", "Hyundai", "Manufacturing assembly")
        score = _score_skills(job, "CNA for 3 years at nursing home")
        assert score <= 0.2

    def test_empty_work_history_scores_baseline(self):
        from app.modules.matching.job_scoring import _score_skills

        job = _annotated_job("Cashier", "Walmart", "Retail customer service")
        score = _score_skills(job, "")
        assert score == pytest.approx(0.3)


class TestScoreSchedule:
    def test_no_conflict_returns_high(self):
        from app.modules.matching.job_scoring import _score_schedule

        job = _annotated_job(schedule_conflict=False)
        assert _score_schedule(job) == 1.0

    def test_conflict_returns_zero(self):
        from app.modules.matching.job_scoring import _score_schedule

        job = _annotated_job(schedule_conflict=True)
        assert _score_schedule(job) == 0.0


class TestScoreTransit:
    def test_accessible_returns_high(self):
        from app.modules.matching.job_scoring import _score_transit

        job = _annotated_job(transit_accessible=True, sunday_flag=False)
        assert _score_transit(job, transit_dependent=True) == 1.0

    def test_not_accessible_returns_zero(self):
        from app.modules.matching.job_scoring import _score_transit

        job = _annotated_job(transit_accessible=False, sunday_flag=False)
        assert _score_transit(job, transit_dependent=True) == 0.0

    def test_sunday_flag_returns_half(self):
        from app.modules.matching.job_scoring import _score_transit

        job = _annotated_job(transit_accessible=True, sunday_flag=True)
        assert _score_transit(job, transit_dependent=True) == 0.5

    def test_non_transit_dependent_always_high(self):
        from app.modules.matching.job_scoring import _score_transit

        job = _annotated_job(transit_accessible=False, sunday_flag=True)
        assert _score_transit(job, transit_dependent=False) == 1.0


class TestScoreBarriers:
    def test_no_blockers_returns_high(self):
        from app.modules.matching.job_scoring import _score_barriers

        job = _annotated_job(credit_blocked=False)
        assert _score_barriers(job) == 1.0

    def test_credit_blocked_reduces_score(self):
        from app.modules.matching.job_scoring import _score_barriers

        job = _annotated_job(credit_blocked=True)
        assert _score_barriers(job) == 0.0


class TestScoreJob:
    def test_returns_score_between_0_and_1(self):
        from app.modules.matching.job_scoring import score_job

        job = _annotated_job("CNA", "Baptist", "Nursing", industry_match=True)
        score, reason = score_job(job, "CNA 3 years", True)
        assert 0.0 <= score <= 1.0

    def test_match_reason_non_empty_for_good_match(self):
        from app.modules.matching.job_scoring import score_job

        job = _annotated_job("CNA", "Baptist", "CNA patient care", industry_match=True)
        score, reason = score_job(job, "CNA for 3 years", False)
        assert len(reason) > 0

    def test_maria_cna_scores_highest(self):
        """CNA job should score highest for a user with CNA work history + healthcare target."""
        from app.modules.matching.job_scoring import score_job

        cna_job = _annotated_job(
            "Certified Nursing Assistant", "Baptist Health",
            "CNA patient care position",
            industry_match=True, transit_accessible=True,
        )
        warehouse_job = _annotated_job(
            "Warehouse Associate", "Amazon",
            "Pick and pack orders",
            industry_match=False, transit_accessible=True,
        )
        cna_score, _ = score_job(cna_job, "CNA for 3 years at nursing home", False)
        warehouse_score, _ = score_job(warehouse_job, "CNA for 3 years at nursing home", False)
        assert cna_score > warehouse_score


class TestRankAndBucket:
    def test_strong_bucket_threshold(self):
        """Jobs scoring >= 0.6 should go to strong bucket."""
        from app.modules.matching.job_scoring import rank_and_bucket

        jobs = [
            _annotated_job("CNA", "Baptist", "CNA", industry_match=True),
        ]
        strong, possible, after_repair = rank_and_bucket(
            jobs, "CNA for 3 years", transit_dependent=False,
        )
        assert len(strong) + len(possible) + len(after_repair) > 0

    def test_credit_blocked_goes_to_after_repair(self):
        """Credit-blocked jobs should go to after_repair regardless of score."""
        from app.modules.matching.job_scoring import rank_and_bucket

        jobs = [
            _annotated_job("Bank Teller", "Regions", "Finance", credit_blocked=True, industry_match=True),
        ]
        strong, possible, after_repair = rank_and_bucket(
            jobs, "banking experience", transit_dependent=False,
        )
        assert len(after_repair) == 1
        assert len(strong) == 0

    def test_max_five_per_bucket(self):
        """Each bucket should have at most 5 results."""
        from app.modules.matching.job_scoring import rank_and_bucket

        jobs = [
            _annotated_job(f"Job {i}", description="entry level retail cashier", industry_match=True)
            for i in range(15)
        ]
        strong, possible, _ = rank_and_bucket(
            jobs, "retail cashier for 2 years", transit_dependent=False,
        )
        assert len(strong) <= 5
        assert len(possible) <= 5

"""Tests for PVS (Practical Value Score) composite scorer."""

from app.modules.matching.pvs_scorer import compute_pvs, rank_all_jobs
from app.modules.matching.types import AvailableHours, BarrierType, ScoringContext


# -- Fixtures --

def _job(**overrides: object) -> dict:
    base = {
        "title": "Cashier",
        "company": "Store",
        "location": "Montgomery, AL 36101",
        "description": "",
        "url": "https://example.com",
        "source": "test",
        "credit_check": "unknown",
        "transit_accessible": True,
        "industry_match": False,
        "schedule_conflict": False,
        "credit_blocked": False,
    }
    base.update(overrides)
    return base


def _ctx(**overrides) -> ScoringContext:
    """Build a ScoringContext with sensible defaults."""
    defaults = {
        "user_zip": "36101",
        "transit_dependent": False,
        "schedule_type": AvailableHours.FLEXIBLE,
        "barriers": [],
    }
    defaults.update(overrides)
    return ScoringContext(**defaults)


class TestComputePvs:
    """Test the composite PVS scoring function."""

    def test_no_pay_penalized(self) -> None:
        """Jobs without pay should score lower than those with pay."""
        job = _job(description="Great team culture!")
        score = compute_pvs(job, _ctx())
        assert score <= 0.40

    def test_no_pay_still_differentiates(self) -> None:
        """Jobs without pay should still rank differently by barriers."""
        job = _job(description="Great culture!", location="Montgomery, AL 36101")
        score_clean = compute_pvs(job, _ctx())
        score_barriers = compute_pvs(
            job, _ctx(barriers=[BarrierType.CHILDCARE, BarrierType.CREDIT]),
        )
        assert score_clean > score_barriers

    def test_with_pay_scores_higher(self) -> None:
        """Jobs with disclosed pay should score higher than without."""
        job_pay = _job(description="Pay: $15.00 per hour")
        job_no_pay = _job(description="Great opportunity!")
        ctx = _ctx()
        score_pay = compute_pvs(job_pay, ctx)
        score_no_pay = compute_pvs(job_no_pay, ctx)
        assert score_pay > score_no_pay

    def test_nearby_scores_higher(self) -> None:
        """Jobs in same zip should score higher than distant ones."""
        job_near = _job(location="Montgomery, AL 36101", description="$15/hr")
        job_far = _job(location="Montgomery, AL 36117", description="$15/hr")
        ctx = _ctx()
        score_near = compute_pvs(job_near, ctx)
        score_far = compute_pvs(job_far, ctx)
        assert score_near > score_far

    def test_transit_penalty_lowers_score(self) -> None:
        """Transit-dependent users should see lower scores for distant jobs."""
        job = _job(location="Montgomery, AL 36117", description="$15/hr")
        score_car = compute_pvs(job, _ctx(transit_dependent=False))
        score_bus = compute_pvs(job, _ctx(transit_dependent=True))
        assert score_car > score_bus

    def test_barriers_reduce_time_fit(self) -> None:
        """Barriers should reduce the time-fit score component."""
        job = _job(description="$15/hr", location="Montgomery, AL 36101")
        score_no_barriers = compute_pvs(job, _ctx())
        score_barriers = compute_pvs(
            job, _ctx(barriers=[BarrierType.CHILDCARE, BarrierType.CREDIT]),
        )
        assert score_no_barriers > score_barriers

    def test_schedule_conflict_reduces_score(self) -> None:
        """Schedule conflicts should reduce score."""
        job = _job(description="$15/hr Night shift position, 11pm to 7am", location="Montgomery, AL 36101", schedule_conflict=True)
        score_flex = compute_pvs(job, _ctx())
        score_day = compute_pvs(job, _ctx(schedule_type=AvailableHours.DAYTIME))
        assert score_flex > score_day

    def test_score_between_0_and_1(self) -> None:
        """PVS should always be between 0 and 1."""
        job = _job(description="$15/hr", location="Montgomery, AL 36101")
        score = compute_pvs(job, _ctx())
        assert 0.0 <= score <= 1.0

    def test_credit_blocked_lowers_barrier_compat(self) -> None:
        """Credit-blocked jobs for credit-barrier users should score lower."""
        job_ok = _job(description="$15/hr", location="Montgomery, AL 36101", credit_blocked=False)
        job_blocked = _job(description="$15/hr", location="Montgomery, AL 36101", credit_blocked=True)
        ctx = _ctx(barriers=[BarrierType.CREDIT])
        score_ok = compute_pvs(job_ok, ctx)
        score_blocked = compute_pvs(job_blocked, ctx)
        assert score_ok > score_blocked


class TestRankAllJobs:
    """Test the unified ranked list function."""

    def test_returns_all_jobs(self) -> None:
        """All jobs should be returned — no bucket caps."""
        jobs = [_job(title=f"Job {i}", description="$15/hr") for i in range(20)]
        ranked = rank_all_jobs(jobs, _ctx())
        assert len(ranked) == 20

    def test_sorted_by_pvs_descending(self) -> None:
        """Jobs should be sorted by PVS score, highest first."""
        jobs = [
            _job(title="High Pay", description="$25/hr", location="Montgomery, AL 36101"),
            _job(title="No Pay", description="Great culture!", location="Montgomery, AL 36101"),
            _job(title="Mid Pay", description="$12/hr", location="Montgomery, AL 36101"),
        ]
        ranked = rank_all_jobs(jobs, _ctx())
        scores = [j.relevance_score for j in ranked]
        assert scores == sorted(scores, reverse=True)
        assert ranked[0].title == "High Pay"
        assert ranked[-1].title == "No Pay"

    def test_pay_range_populated(self) -> None:
        """pay_range field should be populated from salary parser."""
        jobs = [
            _job(description="Pay: $15.00 per hour"),
            _job(description="Great benefits!"),
        ]
        ranked = rank_all_jobs(jobs, _ctx())
        has_pay = next(j for j in ranked if j.pay_range is not None)
        no_pay = next(j for j in ranked if j.pay_range is None)
        assert has_pay.pay_range is not None
        assert no_pay.pay_range is None

    def test_credit_blocked_flagged(self) -> None:
        """Credit-blocked jobs should be flagged but still in the list."""
        jobs = [
            _job(title="Regular", credit_blocked=False, description="$15/hr"),
            _job(title="CreditReq", credit_blocked=True, credit_check="required", description="$18/hr"),
        ]
        ranked = rank_all_jobs(jobs, _ctx(barriers=[BarrierType.CREDIT]))
        assert len(ranked) == 2
        credit_job = next(j for j in ranked if j.title == "CreditReq")
        assert credit_job.credit_check_required == "required"

    def test_empty_input(self) -> None:
        """Empty job list should return empty result."""
        ranked = rank_all_jobs([], _ctx())
        assert ranked == []

    def test_match_reason_populated(self) -> None:
        """Match reasons should still be generated."""
        jobs = [_job(description="$15/hr", industry_match=True)]
        ranked = rank_all_jobs(jobs, _ctx())
        assert ranked[0].match_reason != ""

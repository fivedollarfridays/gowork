"""Tests for cliff-aware PVS scoring — net income replaces gross earnings."""

from app.modules.benefits.types import BenefitsProfile
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


def _profile(**overrides) -> BenefitsProfile:
    """Build a benefits profile with defaults."""
    defaults = {
        "household_size": 3,
        "current_monthly_income": 800,
        "enrolled_programs": ["SNAP", "Section_8"],
        "dependents_under_6": 1,
        "dependents_6_to_17": 0,
    }
    defaults.update(overrides)
    return BenefitsProfile(**defaults)


def _ctx(benefits_profile: BenefitsProfile | None = None) -> ScoringContext:
    """Build a ScoringContext with standard defaults."""
    return ScoringContext(
        user_zip="36101",
        transit_dependent=False,
        schedule_type=AvailableHours.FLEXIBLE,
        barriers=[],
        benefits_profile=benefits_profile,
    )


class TestNetIncomeScoring:
    """PVS uses net income when benefits profile is available."""

    def test_cliff_job_scores_lower_than_safe_job(self) -> None:
        """A job just above the Section 8 cutoff should score lower than one
        just below it, because the housing subsidy loss (~$300/month) exceeds
        the small wage increase."""
        # Section 8 cutoff for HH3: 50% of AMI $54,000 = $27,000/yr = ~$12.98/hr
        profile = _profile(enrolled_programs=["Section_8"])
        safe_job = _job(description="Pay: $12.50 per hour", title="Safe")
        cliff_job = _job(description="Pay: $13.50 per hour", title="Cliff")

        ctx = _ctx(benefits_profile=profile)
        safe_score = compute_pvs(safe_job, ctx)
        cliff_score = compute_pvs(cliff_job, ctx)

        assert safe_score > cliff_score

    def test_cliff_penalizes_vs_gross_scoring(self) -> None:
        """A cliff job PVS with benefits profile should be lower than without."""
        profile = _profile(enrolled_programs=["Section_8"])
        # $13.50/hr crosses Section 8 cutoff for HH3
        cliff_job = _job(description="Pay: $13.50 per hour")

        score_with = compute_pvs(cliff_job, _ctx(benefits_profile=profile))
        score_without = compute_pvs(cliff_job, _ctx())

        assert score_with < score_without

    def test_no_programs_same_as_gross(self) -> None:
        """With no enrolled programs, net income scoring equals gross scoring."""
        profile = _profile(enrolled_programs=[])
        job = _job(description="Pay: $15.00 per hour")

        score_with_profile = compute_pvs(job, _ctx(benefits_profile=profile))
        score_without = compute_pvs(job, _ctx())

        assert score_with_profile == score_without

    def test_undisclosed_salary_still_capped(self) -> None:
        """No-pay ceiling still applies even with benefits profile."""
        profile = _profile()
        job = _job(description="Great culture!")

        score = compute_pvs(job, _ctx(benefits_profile=profile))
        assert score <= 0.25


class TestBackwardCompat:
    """Existing behavior preserved when no benefits profile given."""

    def test_no_profile_uses_gross_earnings(self) -> None:
        """Without benefits_profile, compute_pvs uses gross earnings."""
        job = _job(description="Pay: $15.00 per hour")
        score = compute_pvs(job, _ctx())
        assert 0.0 < score <= 1.0

    def test_none_profile_same_as_omitted(self) -> None:
        """Explicitly passing None is same as omitting."""
        job = _job(description="Pay: $15.00 per hour")
        score_omit = compute_pvs(job, _ctx())
        score_none = compute_pvs(job, _ctx(benefits_profile=None))
        assert score_omit == score_none


class TestCliffImpact:
    """CliffImpact attached to ScoredJobMatch."""

    def test_cliff_impact_present_with_profile(self) -> None:
        """Jobs should have cliff_impact when benefits profile is provided."""
        profile = _profile()
        jobs = [_job(description="Pay: $15.00 per hour")]
        ranked = rank_all_jobs(jobs, _ctx(benefits_profile=profile))
        assert ranked[0].cliff_impact is not None

    def test_cliff_impact_none_without_profile(self) -> None:
        """No cliff_impact when no benefits profile."""
        jobs = [_job(description="Pay: $15.00 per hour")]
        ranked = rank_all_jobs(jobs, _ctx())
        assert ranked[0].cliff_impact is None

    def test_cliff_detected_on_section8_job(self) -> None:
        """A high-wage job should show cliff for Section 8 enrollees."""
        profile = _profile(
            household_size=3,
            current_monthly_income=800,
            enrolled_programs=["Section_8"],
        )
        jobs = [_job(description="Pay: $20.00 per hour", title="HighPay")]
        ranked = rank_all_jobs(jobs, _ctx(benefits_profile=profile))
        impact = ranked[0].cliff_impact
        assert impact is not None
        assert impact.has_cliff is True
        assert impact.severity is not None
        assert "Section_8" in impact.affected_programs

    def test_no_cliff_when_no_benefit_change(self) -> None:
        """No cliff when enrolled programs are unaffected by wage level."""
        # Medicaid always returns $0 in Alabama (no expansion)
        profile = _profile(
            household_size=3,
            current_monthly_income=800,
            enrolled_programs=["Medicaid"],
        )
        jobs = [_job(description="Pay: $9.00 per hour", title="LowPay")]
        ranked = rank_all_jobs(jobs, _ctx(benefits_profile=profile))
        impact = ranked[0].cliff_impact
        assert impact is not None
        assert impact.has_cliff is False
        assert impact.affected_programs == []

    def test_cliff_impact_shows_net_change(self) -> None:
        """cliff_impact should include net monthly change vs current."""
        profile = _profile(current_monthly_income=800)
        jobs = [_job(description="Pay: $15.00 per hour")]
        ranked = rank_all_jobs(jobs, _ctx(benefits_profile=profile))
        impact = ranked[0].cliff_impact
        assert impact is not None
        assert isinstance(impact.net_monthly_change, float)

    def test_cliff_impact_none_for_undisclosed_pay(self) -> None:
        """No cliff_impact for jobs without disclosed salary."""
        profile = _profile()
        jobs = [_job(description="Great culture!")]
        ranked = rank_all_jobs(jobs, _ctx(benefits_profile=profile))
        assert ranked[0].cliff_impact is None


class TestRankingWithCliffs:
    """Jobs sorted correctly accounting for benefit cliffs."""

    def test_safe_job_ranked_above_cliff_job(self) -> None:
        """When ranked, a job below Section 8 cutoff beats one just above it."""
        # Section 8 cutoff for HH3: $27,000/yr (~$12.98/hr)
        profile = _profile(enrolled_programs=["Section_8"])
        jobs = [
            _job(title="CliffJob", description="Pay: $13.50 per hour"),
            _job(title="SafeJob", description="Pay: $12.50 per hour"),
        ]
        ranked = rank_all_jobs(jobs, _ctx(benefits_profile=profile))
        titles = [j.title for j in ranked]
        assert titles.index("SafeJob") < titles.index("CliffJob")

    def test_all_jobs_still_returned(self) -> None:
        """Cliff-aware ranking doesn't drop any jobs."""
        profile = _profile()
        jobs = [_job(title=f"Job{i}", description="$15/hr") for i in range(10)]
        ranked = rank_all_jobs(jobs, _ctx(benefits_profile=profile))
        assert len(ranked) == 10


class TestCoverageEdgeCases:
    """Tests for edge case branches to reach 100% coverage."""

    def test_current_net_zero_when_no_income(self) -> None:
        """_current_net returns 0 when current_monthly_income is 0."""
        profile = _profile(current_monthly_income=0)
        jobs = [_job(description="Pay: $15.00 per hour")]
        ranked = rank_all_jobs(jobs, _ctx(benefits_profile=profile))
        impact = ranked[0].cliff_impact
        assert impact is not None
        # With 0 current income, net change should be positive
        assert impact.net_monthly_change > 0

    def test_salary_range_format_preserved(self) -> None:
        """Jobs with salary ranges preserve raw text in pay_range."""
        profile = _profile()
        jobs = [_job(description="Pay: $12.00 - $15.00 per hour")]
        ranked = rank_all_jobs(jobs, _ctx(benefits_profile=profile))
        assert ranked[0].pay_range is not None
        assert "-" in ranked[0].pay_range or "\u2013" in ranked[0].pay_range

    def test_credit_blocked_with_credit_barrier(self) -> None:
        """_score_barrier_compat returns 0.2 for credit-blocked + CREDIT barrier."""
        profile = _profile()
        ctx = ScoringContext(
            user_zip="36101",
            transit_dependent=False,
            schedule_type=AvailableHours.FLEXIBLE,
            barriers=[BarrierType.CREDIT],
            benefits_profile=profile,
        )
        job_blocked = _job(description="Pay: $10.00 per hour", credit_blocked=True)
        job_ok = _job(description="Pay: $10.00 per hour", credit_blocked=False)
        score_blocked = compute_pvs(job_blocked, ctx)
        score_ok = compute_pvs(job_ok, ctx)
        assert score_blocked < score_ok

    def test_industry_match_in_reason(self) -> None:
        """_build_pvs_reason includes industry match text."""
        profile = _profile()
        jobs = [_job(description="Pay: $15.00 per hour", industry_match=True)]
        ranked = rank_all_jobs(jobs, _ctx(benefits_profile=profile))
        assert "industry" in ranked[0].match_reason.lower()

"""Tests for action plan timeline builder — T31.1."""

from datetime import date

from app.modules.benefits.types import (
    BenefitsEligibility,
    CliffAnalysis,
    CliffPoint,
    CliffSeverity,
    EligibilityConfidence,
    ProgramApplicationInfo,
    ProgramBenefit,
    ProgramEligibility,
    WageStep,
)
from app.modules.criminal.expungement import ExpungementEligibility, ExpungementResult
from app.modules.matching.types import BarrierCard, BarrierSeverity, BarrierType, ScoredJobMatch
from app.modules.matching.types_wioa import (
    DislocatedWorkerStatus,
    WIOAConfidence,
    WIOAEligibility,
)
from app.modules.plan.action_plan import ActionCategory, ActionPlan, build_action_plan


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _app_info() -> ProgramApplicationInfo:
    return ProgramApplicationInfo(
        application_url="https://example.com/apply",
        application_steps=["Step 1"],
        required_documents=["ID"],
        office_name="Montgomery DHR",
        office_address="123 Main St",
        office_phone="334-555-1234",
        processing_time="30 days",
    )


def _eligible_program(name: str = "SNAP", monthly: float = 234.0) -> ProgramEligibility:
    return ProgramEligibility(
        program=name,
        eligible=True,
        confidence=EligibilityConfidence.LIKELY,
        income_threshold=30000,
        income_headroom=5000,
        estimated_monthly_value=monthly,
        reason="Income below threshold",
        application_info=_app_info(),
    )


def _job(title: str = "Cashier", company: str = "Walmart", has_cliff: bool = False) -> ScoredJobMatch:
    return ScoredJobMatch(
        title=title,
        company=company,
        relevance_score=0.8,
        match_reason="Good fit",
        pay_range="$14/hr",
    )


def _wioa() -> WIOAEligibility:
    return WIOAEligibility(
        adult_program=True,
        adult_reasons=["Low income", "Barrier to employment"],
        supportive_services=True,
        ita_training=True,
        dislocated_worker=DislocatedWorkerStatus.INELIGIBLE,
        confidence=WIOAConfidence.LIKELY,
    )


def _expungement_now() -> ExpungementResult:
    return ExpungementResult(
        eligibility=ExpungementEligibility.ELIGIBLE_NOW,
        years_remaining=0,
        steps=["Contact Legal Services Alabama"],
        filing_fee="$300",
        notes="You may be eligible to file now.",
    )


def _expungement_future(years: int = 3) -> ExpungementResult:
    return ExpungementResult(
        eligibility=ExpungementEligibility.ELIGIBLE_FUTURE,
        years_remaining=years,
        steps=[f"Wait {years} more years"],
        filing_fee="$300",
        notes=f"Eligible in approximately {years} years.",
    )


def _cliff_analysis() -> CliffAnalysis:
    return CliffAnalysis(
        wage_steps=[WageStep(wage=10, gross_monthly=1733, benefits_total=800, net_monthly=2533)],
        cliff_points=[
            CliffPoint(
                hourly_wage=15, annual_income=31200, net_monthly_income=2400,
                lost_program="SNAP", monthly_loss=234, severity=CliffSeverity.SEVERE,
            ),
        ],
        current_net_monthly=2533,
        programs=[ProgramBenefit(program="SNAP", monthly_value=234, eligible=True, phase_out_start=25000, phase_out_end=35000, cliff_type="hard")],
        worst_cliff_wage=15.0,
        recovery_wage=18.0,
    )


def _benefits_eligibility(enrolled: list[str] | None = None) -> BenefitsEligibility:
    programs = [_eligible_program("SNAP"), _eligible_program("TANF", 200)]
    ineligible = [
        ProgramEligibility(
            program="Medicaid", eligible=False,
            confidence=EligibilityConfidence.UNLIKELY,
            income_threshold=0, income_headroom=0,
            estimated_monthly_value=0, reason="No expansion",
        ),
    ]
    return BenefitsEligibility(
        eligible_programs=programs,
        ineligible_programs=ineligible,
        total_estimated_monthly=434,
        disclaimer="Estimates only.",
    )


def _barrier_card_criminal(expungement: ExpungementResult | None = None) -> BarrierCard:
    return BarrierCard(
        type=BarrierType.CRIMINAL_RECORD,
        severity=BarrierSeverity.HIGH,
        title="Criminal Record",
        actions=["Contact Legal Services Alabama"],
        expungement=expungement,
    )


# ---------------------------------------------------------------------------
# Structure tests
# ---------------------------------------------------------------------------

class TestActionPlanStructure:
    def test_has_five_phases(self):
        plan = build_action_plan(
            strong_matches=[_job()],
            assessment_date=date(2026, 3, 9),
        )
        assert isinstance(plan, ActionPlan)
        assert len(plan.phases) == 5

    def test_phase_ids(self):
        plan = build_action_plan(assessment_date=date(2026, 3, 9))
        ids = [p.phase_id for p in plan.phases]
        assert ids == ["week_1_2", "month_1", "month_2_3", "month_3_6", "month_6_12"]

    def test_phase_labels(self):
        plan = build_action_plan(assessment_date=date(2026, 3, 9))
        labels = [p.label for p in plan.phases]
        assert "Week 1-2: Immediate Actions" in labels[0]
        assert "Month 1:" in labels[1]

    def test_phase_day_ranges_ordered(self):
        plan = build_action_plan(assessment_date=date(2026, 3, 9))
        for i in range(len(plan.phases) - 1):
            assert plan.phases[i].end_day <= plan.phases[i + 1].start_day

    def test_total_actions_matches(self):
        plan = build_action_plan(
            strong_matches=[_job()],
            benefits_eligibility=_benefits_eligibility(),
            assessment_date=date(2026, 3, 9),
        )
        actual = sum(len(p.actions) for p in plan.phases)
        assert plan.total_actions == actual

    def test_assessment_date_stored(self):
        plan = build_action_plan(assessment_date=date(2026, 3, 9))
        assert plan.assessment_date == "2026-03-09"


# ---------------------------------------------------------------------------
# Career Center
# ---------------------------------------------------------------------------

class TestCareerCenterAction:
    def test_career_center_always_first(self):
        plan = build_action_plan(assessment_date=date(2026, 3, 9))
        week1 = plan.phases[0]
        assert len(week1.actions) >= 1
        assert week1.actions[0].category == ActionCategory.CAREER_CENTER
        assert "Career Center" in week1.actions[0].title

    def test_career_center_has_contact(self):
        plan = build_action_plan(assessment_date=date(2026, 3, 9))
        cc = plan.phases[0].actions[0]
        assert cc.resource_phone is not None


# ---------------------------------------------------------------------------
# Job actions
# ---------------------------------------------------------------------------

class TestJobActions:
    def test_top_jobs_in_week_1(self):
        jobs = [_job("Cashier", "Walmart"), _job("Stocker", "Target"), _job("Driver", "Amazon")]
        plan = build_action_plan(strong_matches=jobs, assessment_date=date(2026, 3, 9))
        week1 = plan.phases[0]
        job_actions = [a for a in week1.actions if a.category == ActionCategory.JOB_APPLICATION]
        assert len(job_actions) == 3
        assert "Cashier" in job_actions[0].title
        assert "Walmart" in job_actions[0].title

    def test_max_three_jobs(self):
        jobs = [_job(f"Job {i}", f"Co {i}") for i in range(5)]
        plan = build_action_plan(strong_matches=jobs, assessment_date=date(2026, 3, 9))
        week1 = plan.phases[0]
        job_actions = [a for a in week1.actions if a.category == ActionCategory.JOB_APPLICATION]
        assert len(job_actions) == 3

    def test_no_jobs_no_job_actions(self):
        plan = build_action_plan(strong_matches=[], assessment_date=date(2026, 3, 9))
        week1 = plan.phases[0]
        job_actions = [a for a in week1.actions if a.category == ActionCategory.JOB_APPLICATION]
        assert len(job_actions) == 0


# ---------------------------------------------------------------------------
# Benefits enrollment actions
# ---------------------------------------------------------------------------

class TestBenefitsActions:
    def test_eligible_programs_in_week_1(self):
        elig = _benefits_eligibility()
        plan = build_action_plan(benefits_eligibility=elig, assessment_date=date(2026, 3, 9))
        week1 = plan.phases[0]
        benefits_actions = [a for a in week1.actions if a.category == ActionCategory.BENEFITS_ENROLLMENT]
        program_names = [a.title for a in benefits_actions]
        assert any("SNAP" in t for t in program_names)
        assert any("TANF" in t for t in program_names)

    def test_enrolled_programs_excluded(self):
        elig = _benefits_eligibility()
        plan = build_action_plan(
            benefits_eligibility=elig,
            enrolled_programs=["SNAP"],
            assessment_date=date(2026, 3, 9),
        )
        week1 = plan.phases[0]
        benefits_actions = [a for a in week1.actions if a.category == ActionCategory.BENEFITS_ENROLLMENT]
        program_names = [a.title for a in benefits_actions]
        assert not any("SNAP" in t for t in program_names)
        assert any("TANF" in t for t in program_names)

    def test_no_eligibility_no_benefits_actions(self):
        plan = build_action_plan(assessment_date=date(2026, 3, 9))
        all_actions = [a for p in plan.phases for a in p.actions]
        benefits = [a for a in all_actions if a.category == ActionCategory.BENEFITS_ENROLLMENT]
        assert len(benefits) == 0

    def test_application_info_in_detail(self):
        elig = _benefits_eligibility()
        plan = build_action_plan(benefits_eligibility=elig, assessment_date=date(2026, 3, 9))
        week1 = plan.phases[0]
        snap_action = next(a for a in week1.actions if "SNAP" in a.title)
        assert snap_action.resource_phone is not None


# ---------------------------------------------------------------------------
# Criminal record / expungement actions
# ---------------------------------------------------------------------------

class TestCriminalActions:
    def test_expungement_eligible_now_in_month_1(self):
        card = _barrier_card_criminal(_expungement_now())
        plan = build_action_plan(barriers=[card], assessment_date=date(2026, 3, 9))
        month1 = plan.phases[1]
        crim_actions = [a for a in month1.actions if a.category == ActionCategory.CRIMINAL_RECORD]
        assert len(crim_actions) >= 1
        assert any("expungement" in a.title.lower() for a in crim_actions)

    def test_expungement_future_in_later_phase(self):
        card = _barrier_card_criminal(_expungement_future(3))
        plan = build_action_plan(barriers=[card], assessment_date=date(2026, 3, 9))
        # 3 years future → month_3_6 or month_6_12
        later_actions = []
        for phase in plan.phases[2:]:  # month_2_3 onwards
            later_actions.extend(a for a in phase.actions if a.category == ActionCategory.CRIMINAL_RECORD)
        assert len(later_actions) >= 1

    def test_not_eligible_no_expungement_action(self):
        exp = ExpungementResult(
            eligibility=ExpungementEligibility.NOT_ELIGIBLE,
            notes="Not eligible.",
        )
        card = _barrier_card_criminal(exp)
        plan = build_action_plan(barriers=[card], assessment_date=date(2026, 3, 9))
        all_actions = [a for p in plan.phases for a in p.actions]
        expunge = [a for a in all_actions if "expungement" in a.title.lower()]
        assert len(expunge) == 0

    def test_no_expungement_data_still_has_legal_aid(self):
        card = _barrier_card_criminal(None)
        plan = build_action_plan(barriers=[card], assessment_date=date(2026, 3, 9))
        week1 = plan.phases[0]
        crim = [a for a in week1.actions if a.category == ActionCategory.CRIMINAL_RECORD]
        assert len(crim) >= 1
        assert any("legal" in a.title.lower() for a in crim)


# ---------------------------------------------------------------------------
# WIOA actions
# ---------------------------------------------------------------------------

class TestWIOAActions:
    def test_wioa_eligible_in_week_1(self):
        plan = build_action_plan(wioa_eligibility=_wioa(), assessment_date=date(2026, 3, 9))
        week1 = plan.phases[0]
        training = [a for a in week1.actions if a.category == ActionCategory.TRAINING]
        assert len(training) >= 1
        assert any("WIOA" in a.title for a in training)

    def test_wioa_not_eligible_no_action(self):
        wioa = WIOAEligibility(
            adult_program=False,
            adult_reasons=[],
            supportive_services=False,
            ita_training=False,
            dislocated_worker=DislocatedWorkerStatus.INELIGIBLE,
            confidence=WIOAConfidence.UNLIKELY,
        )
        plan = build_action_plan(wioa_eligibility=wioa, assessment_date=date(2026, 3, 9))
        all_actions = [a for p in plan.phases for a in p.actions]
        wioa_actions = [a for a in all_actions if "WIOA" in a.title]
        assert len(wioa_actions) == 0


# ---------------------------------------------------------------------------
# Credit actions
# ---------------------------------------------------------------------------

class TestCreditActions:
    def test_credit_barrier_generates_actions(self):
        credit = {"barrier_severity": "moderate", "readiness": {"fico_score": 520}}
        plan = build_action_plan(credit_result=credit, assessment_date=date(2026, 3, 9))
        all_actions = [a for p in plan.phases for a in p.actions]
        credit_actions = [a for a in all_actions if a.category == ActionCategory.CREDIT_REPAIR]
        assert len(credit_actions) >= 1

    def test_no_credit_no_credit_actions(self):
        plan = build_action_plan(assessment_date=date(2026, 3, 9))
        all_actions = [a for p in plan.phases for a in p.actions]
        credit_actions = [a for a in all_actions if a.category == ActionCategory.CREDIT_REPAIR]
        assert len(credit_actions) == 0


# ---------------------------------------------------------------------------
# Cliff actions
# ---------------------------------------------------------------------------

class TestCliffActions:
    def test_cliff_transition_in_stability_phase(self):
        cliff = _cliff_analysis()
        plan = build_action_plan(cliff_analysis=cliff, assessment_date=date(2026, 3, 9))
        stability = plan.phases[4]  # month_6_12
        cliff_actions = [a for a in stability.actions if a.category == ActionCategory.BENEFITS_ENROLLMENT]
        assert len(cliff_actions) >= 1
        assert any("cliff" in a.title.lower() or "transition" in a.title.lower() for a in cliff_actions)

    def test_no_cliff_no_transition_action(self):
        plan = build_action_plan(assessment_date=date(2026, 3, 9))
        stability = plan.phases[4]
        cliff_actions = [a for a in stability.actions if "transition" in a.title.lower()]
        assert len(cliff_actions) == 0


# ---------------------------------------------------------------------------
# Empty plan
# ---------------------------------------------------------------------------

class TestEmptyPlan:
    def test_minimal_plan_still_has_career_center(self):
        """Even with no data, career center action exists."""
        plan = build_action_plan(assessment_date=date(2026, 3, 9))
        assert plan.total_actions >= 1
        assert plan.phases[0].actions[0].category == ActionCategory.CAREER_CENTER

    def test_all_none_inputs(self):
        plan = build_action_plan(
            strong_matches=None,
            benefits_eligibility=None,
            wioa_eligibility=None,
            cliff_analysis=None,
            credit_result=None,
            barriers=None,
            enrolled_programs=None,
            assessment_date=date(2026, 3, 9),
        )
        assert isinstance(plan, ActionPlan)
        assert len(plan.phases) == 5

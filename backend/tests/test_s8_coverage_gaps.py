"""S8 Polish: tests targeting specific uncovered lines across modules.

Each test class addresses a specific coverage gap identified during
the Domain Expansion sweep.
"""

import pytest
from pydantic import ValidationError

from app.modules.benefits.types import BenefitsProfile
from app.modules.feedback.types import VisitFeedbackRequest
from app.modules.matching.types import Resource
from app.modules.outcomes.tracker import OutcomeTracker
from app.modules.outcomes.types import BarrierOutcome, OutcomeRecord
from app.modules.plan.generators_barriers import generate_credit_actions
from app.modules.pathway.stage_builder import wage_tier_label
from app.modules.resources.eligibility import (
    EligibilityStatus,
    check_eligibility,
)


# ---------------------------------------------------------------------------
# Cycle 1: OutcomeTracker.get_all_outcomes (tracker.py line 38)
# ---------------------------------------------------------------------------


class TestOutcomeTrackerGetAll:
    """Cover OutcomeTracker.get_all_outcomes method."""

    def test_get_all_outcomes_empty(self) -> None:
        tracker = OutcomeTracker()
        assert tracker.get_all_outcomes() == []

    def test_get_all_outcomes_returns_all_cities(self) -> None:
        tracker = OutcomeTracker()
        tracker.record_outcome(OutcomeRecord(
            session_id="aaaa0001-bbbb-cccc-dddd-eeeeeeeeeeee",
            signal_type="barrier_resolved",
            city="fort-worth",
        ))
        tracker.record_outcome(OutcomeRecord(
            session_id="aaaa0002-bbbb-cccc-dddd-eeeeeeeeeeee",
            signal_type="barrier_resolved",
            city="montgomery",
        ))
        all_outcomes = tracker.get_all_outcomes()
        assert len(all_outcomes) == 2
        cities = {o.city for o in all_outcomes}
        assert cities == {"fort-worth", "montgomery"}

    def test_get_all_outcomes_preserves_data(self) -> None:
        tracker = OutcomeTracker()
        tracker.record_outcome(OutcomeRecord(
            session_id="aaaa0001-bbbb-cccc-dddd-eeeeeeeeeeee",
            signal_type="barrier_resolved",
            barrier_outcomes=[
                BarrierOutcome(barrier_id="credit", resolved=True, weeks_to_resolve=4),
            ],
            city="fort-worth",
        ))
        outcomes = tracker.get_all_outcomes()
        assert outcomes[0].barrier_outcomes[0].barrier_id == "credit"
        assert outcomes[0].barrier_outcomes[0].weeks_to_resolve == 4


# ---------------------------------------------------------------------------
# Cycle 2: Feedback outcome length validation (types.py line 46)
# ---------------------------------------------------------------------------


class TestFeedbackOutcomeValidation:
    """Cover the validate_outcome_length validator."""

    def test_outcome_item_too_long_rejected(self) -> None:
        """Outcome items over 100 characters should fail validation."""
        with pytest.raises(ValidationError, match="100 characters"):
            VisitFeedbackRequest(
                token="tok-1",
                made_it_to_center=1,
                outcomes=["x" * 101],
                plan_accuracy=1,
            )

    def test_outcome_items_at_boundary_accepted(self) -> None:
        """100-character outcome items should be accepted."""
        req = VisitFeedbackRequest(
            token="tok-1",
            made_it_to_center=1,
            outcomes=["x" * 100],
            plan_accuracy=1,
        )
        assert len(req.outcomes[0]) == 100

    def test_multiple_outcomes_one_too_long(self) -> None:
        """If any single outcome exceeds 100 chars, reject all."""
        with pytest.raises(ValidationError):
            VisitFeedbackRequest(
                token="tok-1",
                made_it_to_center=1,
                outcomes=["ok", "x" * 101, "also ok"],
                plan_accuracy=1,
            )


# ---------------------------------------------------------------------------
# Cycle 3: Low-severity credit actions (generators_barriers.py line 76)
# ---------------------------------------------------------------------------


class TestLowSeverityCreditActions:
    """Cover the branch where severity is set but not moderate/severe/high."""

    def test_low_severity_produces_review_action(self) -> None:
        """Low severity should produce a single 'review credit report' action."""
        result = generate_credit_actions({"barrier_severity": "low"})
        assert len(result) == 1
        phase, action = result[0]
        assert phase == "month_1"
        assert "Review credit report" in action.title

    def test_mild_severity_produces_review_action(self) -> None:
        """Any non-empty severity not in moderate/severe/high triggers review."""
        result = generate_credit_actions({"barrier_severity": "mild"})
        assert len(result) == 1
        _, action = result[0]
        assert "Review credit report" in action.title

    def test_low_severity_with_fico_includes_score(self) -> None:
        """FICO score should appear in detail when available."""
        result = generate_credit_actions({
            "barrier_severity": "low",
            "readiness": {"fico_score": 620},
        })
        _, action = result[0]
        assert "620" in action.detail

    def test_low_severity_without_fico_no_detail(self) -> None:
        """Without FICO score, detail should be None."""
        result = generate_credit_actions({"barrier_severity": "low"})
        _, action = result[0]
        assert action.detail is None

    def test_empty_severity_returns_empty(self) -> None:
        """Empty string severity returns no actions."""
        result = generate_credit_actions({"barrier_severity": ""})
        assert result == []

    def test_none_credit_result_returns_empty(self) -> None:
        """None credit result returns no actions."""
        result = generate_credit_actions(None)
        assert result == []


# ---------------------------------------------------------------------------
# Cycle 4: Eligibility engine edge cases (lines 127, 160)
# ---------------------------------------------------------------------------


def _resource(name: str = "Test Resource", **kw) -> Resource:
    defaults = {
        "id": 1, "name": name, "category": "social_service",
        "subcategory": None, "address": None, "phone": None,
        "url": None, "eligibility": None, "services": None,
        "notes": None,
    }
    defaults.update(kw)
    return Resource(**defaults)


def _profile(**kw) -> BenefitsProfile:
    defaults = {
        "household_size": 3,
        "current_monthly_income": 1500.0,
        "enrolled_programs": [],
        "dependents_under_6": 1,
        "dependents_6_to_17": 0,
    }
    defaults.update(kw)
    return BenefitsProfile(**defaults)


class TestEligibilityEdgeCases:
    """Cover remaining uncovered branches in eligibility engine."""

    def test_twc_child_care_low_income_with_kids(self) -> None:
        """TWC Child Care Services with low income + kids -> likely."""
        r = _resource("TWC Child Care Services, Fort Worth")
        profile = _profile(
            household_size=3,
            current_monthly_income=1500.0,
            dependents_under_6=0,
            dependents_6_to_17=2,
        )
        assert check_eligibility(r, profile) == EligibilityStatus.LIKELY

    def test_twc_child_care_high_income(self) -> None:
        """TWC Child Care with high income -> check."""
        r = _resource("TWC Child Care Services, Fort Worth")
        profile = _profile(
            household_size=3,
            current_monthly_income=5000.0,
            dependents_under_6=0,
            dependents_6_to_17=2,
        )
        assert check_eligibility(r, profile) == EligibilityStatus.CHECK

    def test_twc_child_care_no_children(self) -> None:
        """TWC Child Care without any children -> check."""
        r = _resource("TWC Child Care Services, Fort Worth")
        profile = _profile(
            dependents_under_6=0,
            dependents_6_to_17=0,
        )
        assert check_eligibility(r, profile) == EligibilityStatus.CHECK


# ---------------------------------------------------------------------------
# Cycle 5: Stage builder wage_tier_label fallback (line 30)
# ---------------------------------------------------------------------------


class TestWageTierLabelFallback:
    """Cover the 'Advanced career position' fallback for high wages."""

    def test_high_wage_returns_advanced(self) -> None:
        """Wages above all thresholds should return advanced label."""
        assert wage_tier_label(25.0) == "Advanced career position"

    def test_very_high_wage_returns_advanced(self) -> None:
        assert wage_tier_label(100.0) == "Advanced career position"

    def test_at_22_returns_career_track(self) -> None:
        """22.0 is still within the career-track threshold."""
        assert wage_tier_label(22.0) == "Career-track position"

    def test_just_above_22_returns_advanced(self) -> None:
        assert wage_tier_label(22.01) == "Advanced career position"

    def test_entry_level(self) -> None:
        """Smoke test: low wage returns entry-level."""
        assert wage_tier_label(8.0) == "Entry-level position"

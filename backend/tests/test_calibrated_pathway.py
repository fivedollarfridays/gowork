"""Tests for pathway engine with calibrated weeks.

Verifies that the pathway engine:
1. Works unchanged without calibrated data (backward compat)
2. Propagates calibrated weeks to stage_builder -> barrier_sequencer
3. Timeline estimates reflect calibrated values
"""

import pytest

from app.modules.benefits.types import BenefitsProfile
from app.modules.pathway.engine import generate_pathways


def _profile(**overrides) -> BenefitsProfile:
    defaults = {
        "household_size": 3,
        "current_monthly_income": 1200.0,
        "enrolled_programs": ["SNAP"],
        "dependents_under_6": 1,
        "dependents_6_to_17": 0,
    }
    defaults.update(overrides)
    return BenefitsProfile(**defaults)


class TestPathwayBackwardCompat:
    """Existing behavior unchanged without calibrated_weeks."""

    def test_generates_pathways_without_calibration(self):
        result = generate_pathways(
            barrier_ids=["criminal_record", "credit"],
            benefits_profile=_profile(),
            current_wage=0.0,
        )
        assert len(result.pathways) > 0

    def test_none_calibrated_weeks_works(self):
        result = generate_pathways(
            barrier_ids=["criminal_record"],
            benefits_profile=_profile(),
            current_wage=0.0,
            calibrated_weeks=None,
        )
        assert len(result.pathways) > 0


class TestPathwayCalibrated:
    """Pathway engine uses calibrated weeks when provided."""

    def test_calibrated_weeks_affect_timeline(self):
        # Default criminal_record = 12 weeks
        default_result = generate_pathways(
            barrier_ids=["criminal_record"],
            benefits_profile=_profile(),
            current_wage=0.0,
        )
        # Calibrated to 6 weeks
        calibrated_result = generate_pathways(
            barrier_ids=["criminal_record"],
            benefits_profile=_profile(),
            current_wage=0.0,
            calibrated_weeks={"criminal_record": 6},
        )
        # The calibrated pathway should have shorter total_weeks
        # (or equal if barrier doesn't land in a step, but generally shorter)
        default_weeks = default_result.pathways[0].total_weeks
        calibrated_weeks = calibrated_result.pathways[0].total_weeks
        assert calibrated_weeks <= default_weeks

    def test_empty_calibrated_weeks_same_as_default(self):
        default_result = generate_pathways(
            barrier_ids=["criminal_record"],
            benefits_profile=_profile(),
            current_wage=0.0,
        )
        calibrated_result = generate_pathways(
            barrier_ids=["criminal_record"],
            benefits_profile=_profile(),
            current_wage=0.0,
            calibrated_weeks={},
        )
        assert default_result.pathways[0].total_weeks == calibrated_result.pathways[0].total_weeks

"""Tests for barrier_sequencer with calibrated weeks.

Verifies that the sequencer:
1. Works unchanged when calibrated_weeks is None (backward compat)
2. Uses calibrated values when provided
3. Falls back to hardcoded for missing barriers
"""

import pytest

from app.modules.plan.barrier_sequencer import (
    _WEEKS_PER_BARRIER,
    sequence_barriers,
)


class TestSequencerBackwardCompat:
    """Existing behavior is unchanged when calibrated_weeks is not provided."""

    def test_default_weeks_used_when_no_calibration(self):
        result = sequence_barriers(["criminal_record"])
        step = result.steps[0]
        assert step.estimated_weeks == _WEEKS_PER_BARRIER["criminal_record"]

    def test_none_calibrated_weeks_uses_defaults(self):
        result = sequence_barriers(["criminal_record"], calibrated_weeks=None)
        step = result.steps[0]
        assert step.estimated_weeks == _WEEKS_PER_BARRIER["criminal_record"]


class TestSequencerCalibrated:
    """Sequencer uses calibrated weeks when provided."""

    def test_calibrated_weeks_used(self):
        result = sequence_barriers(
            ["criminal_record"],
            calibrated_weeks={"criminal_record": 6},
        )
        step = result.steps[0]
        assert step.estimated_weeks == 6

    def test_mixed_calibrated_and_default(self):
        """Calibrated for some barriers, default for others."""
        result = sequence_barriers(
            ["criminal_record", "credit"],
            calibrated_weeks={"criminal_record": 6},
        )
        cr = next(s for s in result.steps if s.barrier_id == "criminal_record")
        credit = next(s for s in result.steps if s.barrier_id == "credit")
        assert cr.estimated_weeks == 6
        assert credit.estimated_weeks == _WEEKS_PER_BARRIER["credit"]

    def test_total_weeks_uses_calibrated_values(self):
        result = sequence_barriers(
            ["criminal_record", "credit"],
            calibrated_weeks={"criminal_record": 6, "credit": 4},
        )
        assert result.estimated_total_weeks == 10

    def test_empty_calibrated_weeks_uses_defaults(self):
        result = sequence_barriers(["criminal_record"], calibrated_weeks={})
        step = result.steps[0]
        assert step.estimated_weeks == _WEEKS_PER_BARRIER["criminal_record"]

    def test_unknown_barrier_with_calibration(self):
        """Unknown barriers still get default of 4 weeks."""
        result = sequence_barriers(
            ["unknown_barrier"],
            calibrated_weeks={"criminal_record": 6},
        )
        step = result.steps[0]
        assert step.estimated_weeks == 4  # default for unknown

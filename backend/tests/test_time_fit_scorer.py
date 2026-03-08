"""Tests for time-fit scorer: schedule conflict + barrier time cost analysis."""

import pytest

from app.modules.matching.time_fit_scorer import score_time_fit
from app.modules.matching.types import AvailableHours, BarrierType


class TestTimeFitNoConflictNoBarriers:
    """Cycle 1: baseline — no schedule conflict, no barriers."""

    def test_no_conflict_no_barriers_returns_1(self) -> None:
        job = {"description": "General warehouse position, Monday through Friday"}
        result = score_time_fit(job, AvailableHours.DAYTIME, [])
        assert result == 1.0

    def test_flexible_schedule_no_barriers_returns_1(self) -> None:
        job = {"description": "General warehouse position"}
        result = score_time_fit(job, AvailableHours.FLEXIBLE, [])
        assert result == 1.0

    def test_flexible_ignores_night_shift_conflict(self) -> None:
        job = {"description": "Night shift position, 11pm to 7am"}
        result = score_time_fit(job, AvailableHours.FLEXIBLE, [])
        assert result == 1.0

    def test_evening_no_conflict_returns_1(self) -> None:
        job = {"description": "Customer service representative, flexible hours"}
        result = score_time_fit(job, AvailableHours.EVENING, [])
        assert result == 1.0


class TestTimeFitScheduleConflict:
    """Cycle 2: schedule conflict detection lowers score."""

    def test_schedule_conflict_lowers_score(self) -> None:
        """schedule=0.2, barrier=1.0 -> 0.2*0.6 + 1.0*0.4 = 0.52."""
        job = {"description": "Night shift position", "schedule_conflict": True}
        result = score_time_fit(job, AvailableHours.DAYTIME, [])
        assert result == pytest.approx(0.52, abs=0.01)

    def test_no_conflict_flag_returns_1(self) -> None:
        """schedule=1.0 when schedule_conflict flag is False."""
        job = {"description": "Early morning shift starting 6am", "schedule_conflict": False}
        result = score_time_fit(job, AvailableHours.EVENING, [])
        assert result == 1.0


class TestTimeFitBarrierCost:
    """Cycle 3: barrier time costs reduce score."""

    def test_childcare_and_credit_barriers(self) -> None:
        """schedule=1.0, barrier=1.0-0.4-0.15=0.45 -> 1.0*0.6 + 0.45*0.4 = 0.78."""
        job = {"description": "General warehouse position"}
        barriers = [BarrierType.CHILDCARE, BarrierType.CREDIT]
        result = score_time_fit(job, AvailableHours.DAYTIME, barriers)
        assert result == pytest.approx(0.78, abs=0.01)

    def test_all_seven_barriers_capped_at_max_penalty(self) -> None:
        """Total cost=1.25, capped to 0.6, barrier_score=0.4 -> 1.0*0.6 + 0.4*0.4 = 0.76."""
        job = {"description": "General warehouse position"}
        all_barriers = [
            BarrierType.CHILDCARE,
            BarrierType.TRAINING,
            BarrierType.HEALTH,
            BarrierType.CREDIT,
            BarrierType.TRANSPORTATION,
            BarrierType.HOUSING,
            BarrierType.CRIMINAL_RECORD,
        ]
        result = score_time_fit(job, AvailableHours.DAYTIME, all_barriers)
        # barrier_score = max(1.0 - 1.25, 0.4) = 0.4
        assert result == pytest.approx(0.76, abs=0.01)


class TestTimeFitCombined:
    """Cycle 4: schedule conflict + barrier time cost combined."""

    def test_conflict_with_childcare_and_training(self) -> None:
        """schedule=0.2, barrier=max(1.0-0.65,0.4)=0.4 -> 0.2*0.6 + 0.4*0.4 = 0.28."""
        job = {"description": "Night shift position", "schedule_conflict": True}
        barriers = [BarrierType.CHILDCARE, BarrierType.TRAINING]
        result = score_time_fit(job, AvailableHours.DAYTIME, barriers)
        assert result == pytest.approx(0.28, abs=0.01)

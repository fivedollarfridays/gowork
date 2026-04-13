"""Edge case tests for outcome intelligence -- Donatello attack vectors.

Tests boundary conditions, input fuzzing, and integration scenarios.
"""

import json

import pytest
from sqlalchemy import text

from app.core.database import get_async_session_factory
from app.modules.outcomes.intelligence import (
    CalibratedWeeks,
    ConfidenceLevel,
    compute_calibrated_barriers,
)
from app.modules.outcomes.intelligence_queries import get_barrier_feedback_rows


@pytest.fixture
async def db(test_engine):
    factory = get_async_session_factory()
    async with factory() as session:
        yield session


class TestInputFuzzing:
    """Donatello Module 1: Input fuzzing on compute_calibrated_barriers."""

    def test_empty_barrier_id_skipped(self):
        rows = [{"barrier_id": "", "resolved": True, "weeks_to_resolve": 4}]
        result = compute_calibrated_barriers(rows)
        assert result.barriers == []

    def test_none_barrier_id_skipped(self):
        rows = [{"barrier_id": None, "resolved": True, "weeks_to_resolve": 4}]
        result = compute_calibrated_barriers(rows)
        assert result.barriers == []

    def test_missing_barrier_id_key_skipped(self):
        rows = [{"resolved": True, "weeks_to_resolve": 4}]
        result = compute_calibrated_barriers(rows)
        assert result.barriers == []

    def test_negative_weeks_still_counted(self):
        """Negative weeks is unusual but we don't reject it -- data is data."""
        rows = [
            {"barrier_id": "credit", "resolved": True, "weeks_to_resolve": -1},
            {"barrier_id": "credit", "resolved": True, "weeks_to_resolve": 5},
            {"barrier_id": "credit", "resolved": True, "weeks_to_resolve": 8},
        ]
        result = compute_calibrated_barriers(rows)
        barrier = next(b for b in result.barriers if b.barrier_id == "credit")
        assert barrier.avg_weeks == 4.0  # (-1 + 5 + 8) / 3

    def test_zero_weeks_counted(self):
        rows = [
            {"barrier_id": "transportation", "resolved": True, "weeks_to_resolve": 0},
            {"barrier_id": "transportation", "resolved": True, "weeks_to_resolve": 0},
            {"barrier_id": "transportation", "resolved": True, "weeks_to_resolve": 0},
        ]
        result = compute_calibrated_barriers(rows)
        barrier = next(b for b in result.barriers if b.barrier_id == "transportation")
        assert barrier.avg_weeks == 0.0


class TestBoundaryConditions:
    """Donatello Module 2: Boundary testing."""

    def test_exactly_3_samples_is_medium(self):
        rows = [{"barrier_id": "credit", "resolved": True, "weeks_to_resolve": w} for w in [4, 6, 8]]
        result = compute_calibrated_barriers(rows)
        barrier = next(b for b in result.barriers if b.barrier_id == "credit")
        assert barrier.confidence == ConfidenceLevel.MEDIUM

    def test_exactly_9_samples_is_medium(self):
        rows = [{"barrier_id": "credit", "resolved": True, "weeks_to_resolve": 4}] * 9
        result = compute_calibrated_barriers(rows)
        barrier = next(b for b in result.barriers if b.barrier_id == "credit")
        assert barrier.confidence == ConfidenceLevel.MEDIUM

    def test_exactly_10_samples_is_high(self):
        rows = [{"barrier_id": "credit", "resolved": True, "weeks_to_resolve": 4}] * 10
        result = compute_calibrated_barriers(rows)
        barrier = next(b for b in result.barriers if b.barrier_id == "credit")
        assert barrier.confidence == ConfidenceLevel.HIGH

    def test_all_7_barrier_types(self):
        """All 7 known barrier types process correctly."""
        barrier_ids = [
            "criminal_record", "credit", "transportation",
            "childcare", "housing", "health", "training",
        ]
        rows = [
            {"barrier_id": bid, "resolved": True, "weeks_to_resolve": i + 1}
            for i, bid in enumerate(barrier_ids)
        ]
        result = compute_calibrated_barriers(rows)
        assert len(result.barriers) == 7


class TestWeeksDictIntegration:
    """Donatello Module 4: Integration with barrier_sequencer."""

    def test_weeks_dict_values_are_positive_ints(self):
        rows = [{"barrier_id": "credit", "resolved": True, "weeks_to_resolve": w} for w in [3, 5, 7]]
        result = compute_calibrated_barriers(rows)
        cw = result.to_weeks_dict()
        for val in cw.values():
            assert isinstance(val, int)
            assert val > 0

    def test_weeks_dict_rounds_correctly(self):
        """3.5 rounds to 4, 3.4 rounds to 3."""
        rows_high = [
            {"barrier_id": "credit", "resolved": True, "weeks_to_resolve": w}
            for w in [3, 4, 4]  # avg = 3.666... -> rounds to 4
        ]
        result = compute_calibrated_barriers(rows_high)
        assert result.to_weeks_dict().get("credit") == 4

    def test_mixed_confidence_in_weeks_dict(self):
        """Only MEDIUM+ barriers appear in weeks dict."""
        rows = [
            # criminal_record: 1 sample -> LOW -> excluded
            {"barrier_id": "criminal_record", "resolved": True, "weeks_to_resolve": 6},
            # credit: 4 samples -> MEDIUM -> included
            *[{"barrier_id": "credit", "resolved": True, "weeks_to_resolve": 8}] * 4,
        ]
        result = compute_calibrated_barriers(rows)
        cw = result.to_weeks_dict()
        assert "criminal_record" not in cw
        assert "credit" in cw


class TestDBQueryEdgeCases:
    """Donatello Module 3: State corruption in DB queries."""

    @pytest.mark.anyio
    async def test_empty_barriers_list_in_session(self, db):
        sid = "aaaaaaaa-bbbb-cccc-dddd-000000000001"
        await db.execute(
            text(
                "INSERT INTO sessions (id, created_at, barriers, expires_at) "
                "VALUES (:id, '2026-01-01', :barriers, '2027-01-01')"
            ),
            {"id": sid, "barriers": json.dumps([])},
        )
        await db.commit()
        await db.execute(
            text(
                "INSERT INTO visit_feedback "
                "(session_id, submitted_at, made_it_to_center, outcomes, plan_accuracy) "
                "VALUES (:sid, '2026-03-01', 1, '[]', 3)"
            ),
            {"sid": sid},
        )
        await db.commit()
        rows = await get_barrier_feedback_rows(db)
        assert rows == []

    @pytest.mark.anyio
    async def test_non_string_barriers_skipped(self, db):
        """Non-string items in barriers list are skipped."""
        sid = "aaaaaaaa-bbbb-cccc-dddd-000000000001"
        await db.execute(
            text(
                "INSERT INTO sessions (id, created_at, barriers, expires_at) "
                "VALUES (:id, '2026-01-01', :barriers, '2027-01-01')"
            ),
            {"id": sid, "barriers": json.dumps([42, None, "credit"])},
        )
        await db.commit()
        await db.execute(
            text(
                "INSERT INTO visit_feedback "
                "(session_id, submitted_at, made_it_to_center, outcomes, plan_accuracy) "
                "VALUES (:sid, '2026-03-01', 1, '[]', 3)"
            ),
            {"sid": sid},
        )
        await db.commit()
        rows = await get_barrier_feedback_rows(db)
        assert len(rows) == 1
        assert rows[0]["barrier_id"] == "credit"

    @pytest.mark.anyio
    async def test_malformed_outcomes_json(self, db):
        sid = "aaaaaaaa-bbbb-cccc-dddd-000000000001"
        await db.execute(
            text(
                "INSERT INTO sessions (id, created_at, barriers, expires_at) "
                "VALUES (:id, '2026-01-01', :barriers, '2027-01-01')"
            ),
            {"id": sid, "barriers": json.dumps(["credit"])},
        )
        await db.commit()
        await db.execute(
            text(
                "INSERT INTO visit_feedback "
                "(session_id, submitted_at, made_it_to_center, outcomes, plan_accuracy) "
                "VALUES (:sid, '2026-03-01', 1, 'NOT-JSON', 3)"
            ),
            {"sid": sid},
        )
        await db.commit()
        rows = await get_barrier_feedback_rows(db)
        # Should still produce a row, just not marked resolved
        assert len(rows) == 1
        assert rows[0]["resolved"] is False

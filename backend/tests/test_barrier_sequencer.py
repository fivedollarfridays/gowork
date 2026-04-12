"""Tests for barrier sequencing engine."""

import pytest

from app.modules.plan.sequence_types import BarrierSequence, SequenceStep


class TestBarrierSequencer:
    def test_single_barrier(self):
        """A single barrier should produce one step."""
        from app.modules.plan.barrier_sequencer import sequence_barriers

        result = sequence_barriers(["CREDIT_LOW_SCORE"])
        assert isinstance(result, BarrierSequence)
        assert result.total_barriers == 1
        assert len(result.steps) == 1
        assert result.steps[0].barrier_id == "CREDIT_LOW_SCORE"

    def test_dependent_barriers_ordered(self):
        """CREDIT_NO_BANK -> CREDIT_NO_HISTORY should come before downstream."""
        from app.modules.plan.barrier_sequencer import sequence_barriers

        result = sequence_barriers(["CREDIT_LOW_SCORE", "CREDIT_NO_BANK", "CREDIT_NO_HISTORY"])
        ids = [s.barrier_id for s in result.steps]
        # CREDIT_NO_BANK causes CREDIT_NO_HISTORY causes CREDIT_LOW_SCORE
        assert ids.index("CREDIT_NO_BANK") < ids.index("CREDIT_NO_HISTORY")
        assert ids.index("CREDIT_NO_HISTORY") < ids.index("CREDIT_LOW_SCORE")

    def test_empty_barriers(self):
        """Empty input should produce empty sequence."""
        from app.modules.plan.barrier_sequencer import sequence_barriers

        result = sequence_barriers([])
        assert result.total_barriers == 0
        assert len(result.steps) == 0

    def test_unknown_barrier_handled(self):
        """Unknown barrier IDs should be included but not crash."""
        from app.modules.plan.barrier_sequencer import sequence_barriers

        result = sequence_barriers(["UNKNOWN_BARRIER"])
        assert result.total_barriers == 1
        assert result.steps[0].barrier_id == "UNKNOWN_BARRIER"

    def test_unlocks_populated(self):
        """Steps should list which other barriers they unlock."""
        from app.modules.plan.barrier_sequencer import sequence_barriers

        result = sequence_barriers([
            "CREDIT_NO_BANK", "CREDIT_NO_HISTORY", "CREDIT_LOW_SCORE",
        ])
        bank_step = next(s for s in result.steps if s.barrier_id == "CREDIT_NO_BANK")
        # CREDIT_NO_BANK unlocks CREDIT_NO_HISTORY (CAUSES)
        assert "CREDIT_NO_HISTORY" in bank_step.unlocks

    def test_criminal_record_before_employment(self):
        """Criminal record barriers should resolve before employment gaps."""
        from app.modules.plan.barrier_sequencer import sequence_barriers

        result = sequence_barriers(["CRIMINAL_RECORD", "EMPLOYMENT_GAP"])
        ids = [s.barrier_id for s in result.steps]
        assert ids.index("CRIMINAL_RECORD") < ids.index("EMPLOYMENT_GAP")

    def test_childcare_before_employment(self):
        """Childcare barriers should resolve before employment hours."""
        from app.modules.plan.barrier_sequencer import sequence_barriers

        result = sequence_barriers(["CHILDCARE_DAY", "EMPLOYMENT_LIMITED_HOURS"])
        ids = [s.barrier_id for s in result.steps]
        assert ids.index("CHILDCARE_DAY") < ids.index("EMPLOYMENT_LIMITED_HOURS")

    def test_all_barriers_returns_all(self):
        """All 33 barriers should produce 33 steps."""
        from app.modules.plan.barrier_sequencer import sequence_barriers, _load_graph

        graph = _load_graph()
        all_ids = [b["id"] for b in graph["barriers"]]
        result = sequence_barriers(all_ids)
        assert result.total_barriers == 33
        assert len(result.steps) == 33
        # Full graph has cycles (e.g., employment -> credit -> housing -> employment)
        # which is expected in real barrier networks

    def test_step_has_playbook(self):
        """Each step should have a non-empty playbook."""
        from app.modules.plan.barrier_sequencer import sequence_barriers

        result = sequence_barriers(["CREDIT_LOW_SCORE"])
        assert len(result.steps[0].playbook) > 0

    def test_sequence_order_is_deterministic(self):
        """Same input should produce same output order."""
        from app.modules.plan.barrier_sequencer import sequence_barriers

        ids = ["HOUSING_UNSTABLE", "CREDIT_LOW_SCORE", "EMPLOYMENT_INSTABILITY"]
        r1 = sequence_barriers(ids)
        r2 = sequence_barriers(ids)
        assert [s.barrier_id for s in r1.steps] == [s.barrier_id for s in r2.steps]

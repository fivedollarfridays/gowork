"""Tests for barrier sequencer filtering of non-ordering relationships.

Covers barrier_sequencer.py lines 46, 63 -- the `continue` branches
that skip relationship types not in _ORDERING_RELS.
"""

from app.modules.plan.barrier_sequencer import (
    _build_adjacency,
    _compute_unlocks,
)


class TestNonOrderingRelationships:
    """Verify non-ordering relationship types are properly filtered."""

    def test_co_occurs_excluded_from_adjacency(self):
        """CO_OCCURS rels should not create edges in adjacency list."""
        graph = {
            "barriers": [
                {"id": "A", "name": "A", "category": "test", "playbook": ""},
                {"id": "B", "name": "B", "category": "test", "playbook": ""},
            ],
            "relationships": [
                # Ordering rel (should create edge)
                {"source": "A", "target": "B", "relationship_type": "CAUSES", "weight": 0.5},
                # Non-ordering rel (should be skipped)
                {"source": "B", "target": "A", "relationship_type": "CO_OCCURS", "weight": 0.3},
            ],
        }
        active = {"A", "B"}
        adj, in_deg = _build_adjacency(graph, active)
        # Only A->B from CAUSES, not B->A from CO_OCCURS
        assert "B" in adj.get("A", [])
        assert "A" not in adj.get("B", [])
        assert in_deg["A"] == 0
        assert in_deg["B"] == 1

    def test_co_occurs_excluded_from_unlocks(self):
        """CO_OCCURS rels should not appear in unlocks list."""
        graph = {
            "barriers": [
                {"id": "X", "name": "X", "category": "test", "playbook": ""},
                {"id": "Y", "name": "Y", "category": "test", "playbook": ""},
            ],
            "relationships": [
                {"source": "X", "target": "Y", "relationship_type": "CO_OCCURS", "weight": 0.5},
            ],
        }
        active = {"X", "Y"}
        unlocks = _compute_unlocks("X", graph, active)
        # CO_OCCURS should not count as unlocking
        assert unlocks == []

    def test_mixed_ordering_and_non_ordering(self):
        """Mix of ordering and non-ordering rels."""
        graph = {
            "barriers": [
                {"id": "A", "name": "A", "category": "test", "playbook": ""},
                {"id": "B", "name": "B", "category": "test", "playbook": ""},
                {"id": "C", "name": "C", "category": "test", "playbook": ""},
            ],
            "relationships": [
                {"source": "A", "target": "B", "relationship_type": "CAUSES", "weight": 0.7},
                {"source": "A", "target": "C", "relationship_type": "CORRELATES", "weight": 0.3},
                {"source": "B", "target": "C", "relationship_type": "WORSENS", "weight": 0.5},
            ],
        }
        active = {"A", "B", "C"}
        adj, in_deg = _build_adjacency(graph, active)
        # A->B (CAUSES) and B->C (WORSENS) are ordering
        # A->C (CORRELATES) is not
        assert "B" in adj.get("A", [])
        assert "C" not in adj.get("A", [])
        assert "C" in adj.get("B", [])

        unlocks = _compute_unlocks("A", graph, active)
        # Only B is unlocked by A (CAUSES), not C (CORRELATES)
        assert "B" in unlocks
        assert "C" not in unlocks

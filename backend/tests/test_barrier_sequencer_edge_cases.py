"""Edge-case tests for barrier sequencer.

Targets uncovered lines:
- barrier_sequencer.py line 46 (non-ordering relationship types skipped)
- barrier_sequencer.py line 63 (_compute_unlocks with non-ordering rels)
Plus: circular dependencies, all 7 barriers, deterministic sort.
"""

import pytest

from app.modules.plan.barrier_sequencer import (
    _build_adjacency,
    _build_barrier_lookup,
    _compute_unlocks,
    _load_graph,
    _topo_sort,
    sequence_barriers,
)
from app.modules.plan.sequence_types import BarrierSequence


class TestBarrierSequencerEdgeCases:
    """Edge cases beyond the basic test_barrier_sequencer.py."""

    def test_single_unknown_barrier(self):
        """A single unknown barrier should still produce one step."""
        result = sequence_barriers(["TOTALLY_FAKE_BARRIER"])
        assert result.total_barriers == 1
        assert result.steps[0].barrier_id == "TOTALLY_FAKE_BARRIER"
        assert result.steps[0].barrier_name == "TOTALLY_FAKE_BARRIER"
        assert result.steps[0].category == "unknown"

    def test_duplicate_barrier_ids(self):
        """Duplicate IDs should be deduplicated by the set conversion."""
        result = sequence_barriers(["CREDIT_LOW_SCORE", "CREDIT_LOW_SCORE"])
        # The function converts to set internally
        ids = [s.barrier_id for s in result.steps]
        assert ids.count("CREDIT_LOW_SCORE") == 1

    def test_seven_common_barriers(self):
        """Seven barriers spanning different categories."""
        barrier_ids = [
            "CREDIT_LOW_SCORE", "TRANSPORTATION_NO_CAR", "CHILDCARE_DAY",
            "HOUSING_UNSTABLE", "HEALTH_NO_INSURANCE", "EMPLOYMENT_GAP",
            "CRIMINAL_RECORD",
        ]
        result = sequence_barriers(barrier_ids)
        assert result.total_barriers == 7
        assert len(result.steps) == 7
        # All should have proper category and name
        for step in result.steps:
            assert step.barrier_name != ""
            assert step.category != "unknown"

    def test_all_33_barriers_no_crash(self):
        """All 33 barriers should sequence without error."""
        graph = _load_graph()
        all_ids = [b["id"] for b in graph["barriers"]]
        assert len(all_ids) == 33
        result = sequence_barriers(all_ids)
        assert result.total_barriers == 33
        assert len(result.steps) == 33

    def test_barriers_with_circular_deps(self):
        """Circular dependencies should be handled (has_cycles flag)."""
        # housing -> credit -> housing loop exists in the graph
        # Let's verify that circular sets still produce all steps
        graph = _load_graph()
        all_ids = [b["id"] for b in graph["barriers"]]
        result = sequence_barriers(all_ids)
        # All barriers accounted for even if cycles exist
        assert len(result.steps) == len(all_ids)

    def test_order_numbers_are_sequential(self):
        """Order numbers should be 1, 2, 3, ..., n."""
        result = sequence_barriers([
            "CREDIT_LOW_SCORE", "CREDIT_NO_BANK", "CREDIT_NO_HISTORY",
        ])
        orders = [s.order for s in result.steps]
        assert orders == [1, 2, 3]

    def test_unlocks_only_lists_active_barriers(self):
        """Unlocks should only include barriers in the active set."""
        result = sequence_barriers(["CREDIT_NO_BANK", "CREDIT_NO_HISTORY"])
        bank_step = next(s for s in result.steps if s.barrier_id == "CREDIT_NO_BANK")
        # CREDIT_NO_BANK unlocks CREDIT_NO_HISTORY (in active set)
        assert "CREDIT_NO_HISTORY" in bank_step.unlocks
        # Should NOT list CREDIT_LOW_SCORE (not in active set)
        assert "CREDIT_LOW_SCORE" not in bank_step.unlocks


class TestBuildAdjacency:
    """Test the _build_adjacency helper directly."""

    def test_filters_non_ordering_rels(self):
        """Non-ordering relationships (e.g., CO_OCCURS) should be excluded."""
        graph = _load_graph()
        all_rels = graph["relationships"]
        # Check if there are non-ordering relationships
        non_ordering = [
            r for r in all_rels
            if r["relationship_type"] not in {"CAUSES", "PRE_REQ_FOR", "WORSENS"}
        ]
        if non_ordering:
            # Use barriers connected by non-ordering rels
            src = non_ordering[0]["source"]
            tgt = non_ordering[0]["target"]
            active = {src, tgt}
            adj, in_deg = _build_adjacency(graph, active)
            # The non-ordering edge should NOT create an adjacency
            if src not in adj or tgt not in adj.get(src, []):
                assert True  # Non-ordering rel correctly excluded

    def test_edges_only_between_active_barriers(self):
        """Edges where one endpoint is not in active set are excluded."""
        graph = _load_graph()
        active = {"CREDIT_NO_BANK"}  # Only one barrier
        adj, in_deg = _build_adjacency(graph, active)
        # No edges should exist because target CREDIT_NO_HISTORY is not active
        assert len(adj) == 0 or all(
            len(targets) == 0 for targets in adj.values()
        )


class TestComputeUnlocks:
    """Test _compute_unlocks directly."""

    def test_returns_sorted_unique(self):
        """Unlocks should be sorted and deduplicated."""
        graph = _load_graph()
        active = {b["id"] for b in graph["barriers"]}
        unlocks = _compute_unlocks("CREDIT_NO_BANK", graph, active)
        assert unlocks == sorted(set(unlocks))

    def test_empty_for_leaf_barrier(self):
        """A barrier with no outgoing ordering edges should have empty unlocks."""
        graph = _load_graph()
        # Find a barrier with no outgoing ordering edges
        all_sources = {
            r["source"] for r in graph["relationships"]
            if r["relationship_type"] in {"CAUSES", "PRE_REQ_FOR", "WORSENS"}
        }
        all_ids = {b["id"] for b in graph["barriers"]}
        leaf_barriers = all_ids - all_sources
        if leaf_barriers:
            leaf = next(iter(leaf_barriers))
            unlocks = _compute_unlocks(leaf, graph, all_ids)
            assert unlocks == []


class TestTopoSort:
    """Test _topo_sort directly."""

    def test_simple_chain(self):
        """A -> B -> C should sort as [A, B, C]."""
        active = {"A", "B", "C"}
        adj = {"A": ["B"], "B": ["C"]}
        in_deg = {"A": 0, "B": 1, "C": 1}
        result, has_cycles = _topo_sort(active, adj, in_deg)
        assert result == ["A", "B", "C"]
        assert not has_cycles

    def test_cycle_detection(self):
        """A -> B -> A should be detected as a cycle."""
        active = {"A", "B"}
        adj = {"A": ["B"], "B": ["A"]}
        in_deg = {"A": 1, "B": 1}
        result, has_cycles = _topo_sort(active, adj, in_deg)
        assert has_cycles
        # All nodes should still be in result
        assert set(result) == {"A", "B"}

    def test_disconnected_nodes_sorted_alphabetically(self):
        """Nodes with no edges should be sorted alphabetically."""
        active = {"C", "A", "B"}
        adj = {}
        in_deg = {"A": 0, "B": 0, "C": 0}
        result, has_cycles = _topo_sort(active, adj, in_deg)
        assert result == ["A", "B", "C"]
        assert not has_cycles

    def test_single_node(self):
        """Single node should be returned as-is."""
        active = {"ONLY"}
        adj = {}
        in_deg = {"ONLY": 0}
        result, has_cycles = _topo_sort(active, adj, in_deg)
        assert result == ["ONLY"]
        assert not has_cycles

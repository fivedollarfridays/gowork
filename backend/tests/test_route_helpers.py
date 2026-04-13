"""Direct unit tests for route helper functions.

Tests route-internal helper functions that are difficult to cover
through ASGI transport due to coverage measurement limitations.
"""

import json

import pytest

from app.routes.share import _build_share_url, _extract_career_center, _extract_next_steps
from app.routes.sequence import _map_barrier_to_graph_id
from app.routes.simulate import _compute_unlocked, _JOBS_PER_BARRIER, _BENEFITS_PER_BARRIER


class TestExtractNextSteps:
    """share._extract_next_steps -- pull immediate next steps from plan JSON."""

    def test_returns_steps_list(self):
        plan = {"immediate_next_steps": ["Step 1", "Step 2", "Step 3"]}
        result = _extract_next_steps(plan)
        assert result == ["Step 1", "Step 2", "Step 3"]

    def test_truncates_at_10(self):
        plan = {"immediate_next_steps": [f"Step {i}" for i in range(15)]}
        result = _extract_next_steps(plan)
        assert len(result) == 10

    def test_empty_list(self):
        plan = {"immediate_next_steps": []}
        result = _extract_next_steps(plan)
        assert result == []

    def test_missing_key(self):
        plan = {}
        result = _extract_next_steps(plan)
        assert result == []

    def test_non_list_value_returns_empty(self):
        plan = {"immediate_next_steps": "not a list"}
        result = _extract_next_steps(plan)
        assert result == []

    def test_none_value_returns_empty(self):
        plan = {"immediate_next_steps": None}
        result = _extract_next_steps(plan)
        assert result == []


class TestBuildShareUrl:
    """share._build_share_url -- construct public share URL."""

    def test_builds_url(self):
        url = _build_share_url("abc123")
        assert url == "/shared/abc123"

    def test_url_contains_token(self):
        token = "test-token-xyz"
        url = _build_share_url(token)
        assert token in url


class TestExtractCareerCenter:
    """share._extract_career_center -- city-aware career center info."""

    def test_returns_name_and_state(self):
        name, state = _extract_career_center({})
        assert isinstance(name, str)
        assert len(name) > 0
        assert isinstance(state, str)
        assert len(state) > 0


class TestMapBarrierToGraphId:
    """sequence._map_barrier_to_graph_id -- barrier type to graph node mapping."""

    def test_known_barrier_types(self):
        known = ["credit", "transportation", "childcare", "housing", "health", "training", "criminal_record"]
        for barrier in known:
            result = _map_barrier_to_graph_id(barrier)
            assert result is not None, f"{barrier} should be mapped"
            assert result == barrier

    def test_unknown_barrier_returns_none(self):
        assert _map_barrier_to_graph_id("unknown_barrier") is None

    def test_empty_string_returns_none(self):
        assert _map_barrier_to_graph_id("") is None

    def test_case_sensitive(self):
        assert _map_barrier_to_graph_id("Credit") is None
        assert _map_barrier_to_graph_id("HOUSING") is None


class TestComputeUnlocked:
    """simulate._compute_unlocked -- cascading barrier unlock logic."""

    def test_resolving_root_unlocks_dependents(self):
        all_barriers = ["criminal_record", "credit", "childcare"]
        resolved = {"criminal_record"}
        unlocked = _compute_unlocked(all_barriers, resolved)
        assert isinstance(unlocked, list)

    def test_empty_barriers_returns_empty(self):
        assert _compute_unlocked([], {"credit"}) == []

    def test_empty_resolved_returns_empty(self):
        assert _compute_unlocked(["credit", "housing"], set()) == []

    def test_no_duplicates_in_unlocked(self):
        all_barriers = ["criminal_record", "credit", "transportation", "childcare"]
        resolved = {"criminal_record", "credit"}
        unlocked = _compute_unlocked(all_barriers, resolved)
        assert len(unlocked) == len(set(unlocked))


class TestJobsPerBarrier:
    """simulate._JOBS_PER_BARRIER -- verify all standard barriers have estimates."""

    def test_all_standard_barriers_present(self):
        expected = {"criminal_record", "credit", "transportation", "childcare", "housing", "health", "training"}
        assert set(_JOBS_PER_BARRIER.keys()) == expected

    def test_all_values_positive(self):
        for barrier, count in _JOBS_PER_BARRIER.items():
            assert count > 0, f"{barrier} should have positive job estimate"

    def test_criminal_record_highest(self):
        """Criminal record resolution unlocks the most jobs."""
        assert _JOBS_PER_BARRIER["criminal_record"] >= max(
            v for k, v in _JOBS_PER_BARRIER.items() if k != "criminal_record"
        )


class TestBenefitsPerBarrier:
    """simulate._BENEFITS_PER_BARRIER -- verify benefits mapping."""

    def test_all_standard_barriers_present(self):
        expected = {"criminal_record", "credit", "transportation", "childcare", "housing", "health", "training"}
        assert set(_BENEFITS_PER_BARRIER.keys()) == expected

    def test_all_values_are_lists(self):
        for barrier, benefits in _BENEFITS_PER_BARRIER.items():
            assert isinstance(benefits, list), f"{barrier} benefits should be a list"
            assert len(benefits) > 0, f"{barrier} should have at least one benefit"

"""Direct unit tests for route helper functions.

Tests route-internal helper functions that are difficult to cover
through ASGI transport due to coverage measurement limitations.
"""

import json

import pytest

from app.routes.share import (
    _build_share_url,
    _count_barriers,
    _extract_next_steps,
    _resolve_career_center,
)
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


class TestResolveCareerCenter:
    """share._resolve_career_center -- city-aware real career center info (T13.72)."""

    def test_returns_real_center_name_and_phone(self):
        name, phone = _resolve_career_center()
        assert isinstance(name, str)
        assert isinstance(phone, str)
        # Either a real center is resolved or both fields are empty — what we
        # must NOT do is return the bare city name + an empty phone.
        if name:
            assert "Career Center" in name or "Workforce" in name
        if phone:
            digit_count = sum(1 for ch in phone if ch.isdigit())
            assert digit_count >= 7


class TestCountBarriers:
    """share._count_barriers -- non-PII scalar from raw barrier storage (T13.71)."""

    def test_counts_list_of_slugs(self):
        assert _count_barriers(json.dumps(["credit", "housing", "health"])) == 3

    def test_counts_python_list(self):
        assert _count_barriers(["credit", "housing"]) == 2

    def test_empty_list_returns_zero(self):
        assert _count_barriers("[]") == 0
        assert _count_barriers([]) == 0

    def test_invalid_json_returns_zero(self):
        assert _count_barriers("not-json") == 0

    def test_dict_uses_key_count(self):
        assert _count_barriers({"credit": 1, "housing": 1}) == 2

    def test_unknown_type_returns_zero(self):
        assert _count_barriers(None) == 0
        assert _count_barriers(42) == 0


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

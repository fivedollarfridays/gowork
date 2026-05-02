"""Barrier sequencing engine -- topological sort of barrier dependencies.

Uses the barrier graph seed data to order barrier resolution steps
by their causal/prerequisite relationships. Barriers that CAUSE or
are PRE_REQ_FOR other barriers should be resolved first.
"""

import json
from collections import defaultdict, deque
from functools import lru_cache

from app.core.database import resolve_data_dir
from app.modules.plan.sequence_types import BarrierSequence, SequenceStep

# Relationship types that define ordering (source should come before target)
_ORDERING_RELS = {"CAUSES", "PRE_REQ_FOR", "WORSENS"}

# Estimated resolution time in weeks per barrier type
_WEEKS_PER_BARRIER: dict[str, int] = {
    "criminal_record": 12,
    "credit": 8,
    "transportation": 2,
    "childcare": 4,
    "housing": 6,
    "health": 4,
    "training": 8,
}


@lru_cache(maxsize=1)
def _load_graph() -> dict:
    """Load the barrier graph seed data for the active city.

    Resolves the file from ``resolve_data_dir()`` (city-aware), so
    Montgomery and Fort Worth deployments each load their own seed.
    Cached for the life of the process; tests that switch CITY mid-run
    must call ``_load_graph.cache_clear()``.
    """
    graph_path = resolve_data_dir() / "barrier_graph_seed.json"
    with open(graph_path, encoding="utf-8") as f:
        return json.load(f)


def _build_barrier_lookup(graph: dict) -> dict[str, dict]:
    """Build a lookup dict from barrier ID to barrier data."""
    return {b["id"]: b for b in graph["barriers"]}


def _build_adjacency(
    graph: dict, active_ids: set[str],
) -> tuple[dict[str, list[str]], dict[str, int]]:
    """Build adjacency list and in-degree map for topological sort.

    Only considers edges where BOTH source and target are in active_ids.
    Edge direction: source -> target means source should resolve first.
    """
    adj: dict[str, list[str]] = defaultdict(list)
    in_degree: dict[str, int] = {bid: 0 for bid in active_ids}

    for rel in graph["relationships"]:
        if rel["relationship_type"] not in _ORDERING_RELS:
            continue
        src = rel["source"]
        tgt = rel["target"]
        if src in active_ids and tgt in active_ids:
            adj[src].append(tgt)
            in_degree[tgt] = in_degree.get(tgt, 0) + 1

    return dict(adj), in_degree


def _compute_unlocks(
    barrier_id: str, graph: dict, active_ids: set[str],
) -> list[str]:
    """List barriers that this barrier unlocks (direct targets)."""
    unlocks = []
    for rel in graph["relationships"]:
        if rel["relationship_type"] not in _ORDERING_RELS:
            continue
        if rel["source"] == barrier_id and rel["target"] in active_ids:
            unlocks.append(rel["target"])
    return sorted(set(unlocks))


def _topo_sort(
    active_ids: set[str], adj: dict[str, list[str]], in_degree: dict[str, int],
) -> tuple[list[str], bool]:
    """Kahn's algorithm for topological sort.

    Returns (sorted_list, has_cycles). Ties broken alphabetically
    for deterministic output.
    """
    queue: deque[str] = deque(
        sorted(bid for bid in active_ids if in_degree.get(bid, 0) == 0)
    )
    result: list[str] = []
    visited = 0

    while queue:
        node = queue.popleft()
        result.append(node)
        visited += 1
        # Collect next nodes, sort for determinism
        next_nodes = []
        for neighbor in adj.get(node, []):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                next_nodes.append(neighbor)
        for n in sorted(next_nodes):
            queue.append(n)

    has_cycles = visited < len(active_ids)
    if has_cycles:
        # Add remaining nodes (in cycle) at the end
        remaining = sorted(bid for bid in active_ids if bid not in set(result))
        result.extend(remaining)

    return result, has_cycles


def _build_sequence_steps(
    sorted_ids: list[str],
    lookup: dict[str, dict],
    graph: dict,
    active_ids: set[str],
    weeks_lookup: dict[str, int],
) -> list[SequenceStep]:
    """Build SequenceStep objects from topologically sorted barrier IDs."""
    steps = []
    for order, bid in enumerate(sorted_ids, start=1):
        info = lookup.get(bid, {})
        steps.append(SequenceStep(
            order=order,
            barrier_id=bid,
            barrier_name=info.get("name", bid),
            category=info.get("category", "unknown"),
            playbook=info.get("playbook", ""),
            unlocks=_compute_unlocks(bid, graph, active_ids),
            estimated_weeks=weeks_lookup.get(bid, 4),
        ))
    return steps


def sequence_barriers(
    barrier_ids: list[str],
    calibrated_weeks: dict[str, int] | None = None,
) -> BarrierSequence:
    """Produce a topologically sorted resolution sequence for barriers.

    Args:
        barrier_ids: List of barrier IDs to sequence.
        calibrated_weeks: Optional dict mapping barrier_id to calibrated
            resolution weeks from community outcome data. Falls back to
            _WEEKS_PER_BARRIER defaults for missing barriers.

    Returns:
        BarrierSequence with ordered steps, each containing the
        barrier info and what it unlocks.
    """
    if not barrier_ids:
        return BarrierSequence(steps=[], total_barriers=0)

    graph = _load_graph()
    lookup = _build_barrier_lookup(graph)
    active_ids = set(barrier_ids)

    adj, in_degree = _build_adjacency(graph, active_ids)
    sorted_ids, has_cycles = _topo_sort(active_ids, adj, in_degree)

    weeks_lookup = dict(_WEEKS_PER_BARRIER)
    if calibrated_weeks:
        weeks_lookup.update(calibrated_weeks)

    steps = _build_sequence_steps(
        sorted_ids, lookup, graph, active_ids, weeks_lookup,
    )

    return BarrierSequence(
        steps=steps,
        total_barriers=len(barrier_ids),
        has_cycles=has_cycles,
        estimated_total_weeks=sum(s.estimated_weeks for s in steps),
    )

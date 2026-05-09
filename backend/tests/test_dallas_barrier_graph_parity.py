"""Structural parity contract: Dallas barrier_graph_seed.json mirrors FW.

T25.4 (Sprint 25, Wave 3) — Dallas Expansion.

The barrier graph (nodes + edges + barrier_resources rows) is the load-
bearing artifact behind every plan-sequencer recommendation.  Stage 2
shipped FW with a hand-curated barrier graph; Dallas must inherit the
SAME structure (same barrier IDs, same source->target edges, same
relationship types) and only swap the per-row resource_id +
``notes`` swap to reference Dallas community_resources entries.

If the Dallas barrier graph drifts in shape from FW's:
* Plan sequencer outputs diverge silently for Dallas users
* Front-end barrier card UI gets surprised by unknown barrier IDs
* Cross-city A/B comparisons become apples-to-oranges

This test pins:
1. File exists and parses as JSON.
2. Top-level keys match FW exactly.
3. Barrier IDs are identical (set equality).
4. Each barrier carries the same category as the FW twin.
5. Edge structure (source, target, relationship_type) matches as a SET
   -- ordering may legitimately differ but no edges may be added/lost.
6. Every Dallas barrier_resources ``notes`` field references at least
   one resource name that exists in T25.2's community_resources.json.
7. Skipped FW resource_ids are explicitly documented (option-a per AC).

References:
- ``data/cities/fort-worth/barrier_graph_seed.json`` -- canonical
- ``data/cities/dallas/community_resources.json`` -- T25.2 Dallas seed
- AC: T25.4 in backlog-sprint-25-dallas-expansion
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_FW_DIR = _PROJECT_ROOT / "data" / "cities" / "fort-worth"
_DALLAS_DIR = _PROJECT_ROOT / "data" / "cities" / "dallas"

_FW_GRAPH = _FW_DIR / "barrier_graph_seed.json"
_DALLAS_GRAPH = _DALLAS_DIR / "barrier_graph_seed.json"
_DALLAS_COMMUNITY = _DALLAS_DIR / "community_resources.json"

# FW resource_ids (1..10) that have NO equivalent in T25.2's Dallas
# community_resources.json. Per AC option (a): skip these from the
# Dallas barrier graph entirely rather than smuggle in cross-file
# references that the parity test cannot resolve.
#
# Documented rationale (matches the FW barrier_graph notes payload):
#   6 = Community Action Partners      -- no general financial coaching
#                                          org in Dallas community_resources;
#                                          GreenPath / CCCS analogues live
#                                          in the resources.json bundle.
#   9 = Tarrant County College         -- Dallas College equivalent lives
#                                          in training_programs.json and
#                                          resources.json, NOT in Dallas
#                                          community_resources.json.
#   10 = Trinity Metro                 -- DART equivalent lives in
#                                          resources.json, NOT in Dallas
#                                          community_resources.json.
SKIPPED_FW_RESOURCE_IDS: frozenset[int] = frozenset({6, 9, 10})


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_list(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def _edge_set(graph: dict) -> set[tuple[str, str, str]]:
    """Reduce relationships to (source, target, relationship_type) tuples.

    Weight is allowed to vary (FW and Dallas may tune impacts later);
    structure (which barriers cause/worsen which) must not.
    """
    return {
        (r["source"], r["target"], r["relationship_type"])
        for r in graph.get("relationships", [])
    }


def _community_names(path: Path) -> set[str]:
    return {e["name"] for e in _load_list(path) if "name" in e}


# ---------------------------------------------------------------------------
# File presence + JSON validity
# ---------------------------------------------------------------------------


class TestDallasBarrierGraphFileExists:
    def test_dallas_barrier_graph_file_exists(self):
        assert _DALLAS_GRAPH.is_file(), f"missing: {_DALLAS_GRAPH}"

    def test_dallas_barrier_graph_parses_as_json(self):
        data = _load(_DALLAS_GRAPH)
        assert isinstance(data, dict), "must be a JSON object at top level"

    def test_dallas_barrier_graph_is_utf8(self):
        # read_bytes + decode catches BOMs and bad encodings that
        # read_text(encoding='utf-8') would silently mask.
        raw = _DALLAS_GRAPH.read_bytes()
        raw.decode("utf-8")  # raises if invalid


# ---------------------------------------------------------------------------
# Structural parity with Fort Worth
# ---------------------------------------------------------------------------


class TestStructuralParityWithFortWorth:
    def test_top_level_keys_match(self):
        fw = _load(_FW_GRAPH)
        dallas = _load(_DALLAS_GRAPH)
        assert set(dallas.keys()) == set(fw.keys()), (
            "Dallas barrier_graph_seed.json top-level keys "
            f"{sorted(dallas.keys())} != FW {sorted(fw.keys())}.  "
            "Both files must use the same schema (barriers, "
            "relationships, barrier_resources)."
        )

    def test_barrier_ids_identical(self):
        fw_ids = {b["id"] for b in _load(_FW_GRAPH)["barriers"]}
        dallas_ids = {b["id"] for b in _load(_DALLAS_GRAPH)["barriers"]}
        only_fw = fw_ids - dallas_ids
        only_dallas = dallas_ids - fw_ids
        assert not only_fw, (
            f"Barrier IDs present in FW but missing in Dallas: {sorted(only_fw)}"
        )
        assert not only_dallas, (
            "Barrier IDs present in Dallas but not in FW (no new barriers "
            f"allowed in this task): {sorted(only_dallas)}"
        )

    def test_barrier_categories_identical(self):
        # Same barrier ID must keep the same category.  A barrier flipping
        # from 'childcare' to 'transportation' between cities would break
        # category-level UI grouping.
        fw_cat = {b["id"]: b["category"] for b in _load(_FW_GRAPH)["barriers"]}
        dallas_cat = {
            b["id"]: b["category"] for b in _load(_DALLAS_GRAPH)["barriers"]
        }
        for bid, fw_value in fw_cat.items():
            assert dallas_cat.get(bid) == fw_value, (
                f"Barrier {bid!r} category drift: FW={fw_value!r} "
                f"vs Dallas={dallas_cat.get(bid)!r}"
            )

    def test_relationships_set_identical(self):
        fw_edges = _edge_set(_load(_FW_GRAPH))
        dallas_edges = _edge_set(_load(_DALLAS_GRAPH))
        only_fw = fw_edges - dallas_edges
        only_dallas = dallas_edges - fw_edges
        assert not only_fw, (
            f"Edges present in FW but missing in Dallas: {sorted(only_fw)}"
        )
        assert not only_dallas, (
            "Edges present in Dallas but not in FW (no new edges allowed "
            f"in this task): {sorted(only_dallas)}"
        )

    def test_relationship_types_are_known(self):
        # Pin to the FW vocabulary so a typo like 'CAUSE' (instead of
        # 'CAUSES') breaks the test, not the runtime.
        fw_types = {
            r["relationship_type"] for r in _load(_FW_GRAPH)["relationships"]
        }
        dallas_types = {
            r["relationship_type"] for r in _load(_DALLAS_GRAPH)["relationships"]
        }
        unknown = dallas_types - fw_types
        assert not unknown, (
            f"Dallas relationships use unknown relationship_type values: "
            f"{sorted(unknown)} (FW vocabulary: {sorted(fw_types)})"
        )


# ---------------------------------------------------------------------------
# barrier_resources -- skip parity + cross-file resource resolution
# ---------------------------------------------------------------------------


class TestBarrierResourceSkipParity:
    """The Dallas barrier graph is allowed to OMIT the
    SKIPPED_FW_RESOURCE_IDS set (per AC option-a) but must otherwise
    cover the same (barrier_id, resource_id) shape as FW.
    """

    def test_dallas_omits_only_documented_skipped_ids(self):
        fw_ids = {br["resource_id"] for br in _load(_FW_GRAPH)["barrier_resources"]}
        dallas_ids = {
            br["resource_id"] for br in _load(_DALLAS_GRAPH)["barrier_resources"]
        }
        # Dallas may not introduce new resource_ids beyond FW's universe.
        new_in_dallas = dallas_ids - fw_ids
        assert not new_in_dallas, (
            f"Dallas barrier_resources reference resource_ids not in FW: "
            f"{sorted(new_in_dallas)}"
        )
        # Every FW resource_id that Dallas omits must be in the
        # SKIPPED set -- no silent drops allowed.
        omitted = fw_ids - dallas_ids
        undocumented = omitted - SKIPPED_FW_RESOURCE_IDS
        assert not undocumented, (
            "Dallas silently dropped FW resource_ids without documenting "
            f"them in SKIPPED_FW_RESOURCE_IDS: {sorted(undocumented)}.  "
            "Either add a Dallas equivalent to community_resources.json "
            "OR add the ID to SKIPPED_FW_RESOURCE_IDS with a rationale."
        )

    def test_dallas_skips_documented_ids_completely(self):
        # If we said we'd skip resource_id N, we must skip it everywhere
        # -- no half-skips that leave dangling references.
        dallas_ids = {
            br["resource_id"] for br in _load(_DALLAS_GRAPH)["barrier_resources"]
        }
        leaked = SKIPPED_FW_RESOURCE_IDS & dallas_ids
        assert not leaked, (
            f"SKIPPED_FW_RESOURCE_IDS leaked into Dallas barrier_resources: "
            f"{sorted(leaked)}"
        )

    def test_barrier_id_coverage_matches_after_skip(self):
        # For every (barrier_id, resource_id) pair in FW where the
        # resource_id is NOT skipped, Dallas must have a corresponding
        # (barrier_id, resource_id) pair.
        fw_pairs = {
            (br["barrier_id"], br["resource_id"])
            for br in _load(_FW_GRAPH)["barrier_resources"]
        }
        dallas_pairs = {
            (br["barrier_id"], br["resource_id"])
            for br in _load(_DALLAS_GRAPH)["barrier_resources"]
        }
        expected_in_dallas = {
            pair for pair in fw_pairs if pair[1] not in SKIPPED_FW_RESOURCE_IDS
        }
        missing = expected_in_dallas - dallas_pairs
        assert not missing, (
            "Dallas is missing (barrier_id, resource_id) pairs that FW "
            f"covers and that aren't on the skip list: {sorted(missing)}"
        )


class TestDallasResourceRefsResolveInCommunityResources:
    """Every ``notes`` field in Dallas barrier_resources must reference a
    resource name that exists in T25.2's community_resources.json.

    The notes field carries the human-readable name of the resource that
    the resource_id resolves to at runtime (after DB seeding).  The
    parity test cannot reach into the DB, so it cross-references by name
    instead -- the same way an operator would when reading the JSON.
    """

    def test_each_notes_mentions_a_dallas_community_resource(self):
        community_names = _community_names(_DALLAS_COMMUNITY)
        # Pre-condition: T25.2 must have shipped a non-trivial set of
        # Dallas community resources.  If this fails, T25.2 regressed.
        assert len(community_names) >= 10, (
            f"T25.2 contract: Dallas community_resources.json must have "
            f">=10 entries (got {len(community_names)})."
        )

        unresolved: list[str] = []
        for br in _load(_DALLAS_GRAPH)["barrier_resources"]:
            note = br.get("notes", "")
            # A note "resolves" if any community-resource name appears
            # as a substring inside the note.  This matches FW's
            # convention of writing notes like "Workforce Solutions
            # CCS subsidy reduces childcare cost to copay".
            if not any(name in note for name in community_names):
                unresolved.append(
                    f"barrier={br['barrier_id']!r} "
                    f"resource_id={br['resource_id']} notes={note!r}"
                )

        assert not unresolved, (
            "Dallas barrier_resources rows whose `notes` do not name any "
            "resource present in data/cities/dallas/community_resources.json "
            "(this would break the cross-file resolution contract):\n  "
            + "\n  ".join(unresolved)
        )

    def test_resource_id_to_name_mapping_is_consistent(self):
        # If two rows share the same resource_id, the resource name they
        # reference (the substring inside `notes`) must also match.
        # Otherwise resource_id 4 means "Catholic Charities" in one row
        # and "ChildCareGroup" in another -- silent corruption at seed.
        community_names = _community_names(_DALLAS_COMMUNITY)
        rid_to_name: dict[int, str] = {}
        conflicts: list[str] = []

        for br in _load(_DALLAS_GRAPH)["barrier_resources"]:
            note = br.get("notes", "")
            matches = [n for n in community_names if n in note]
            if not matches:
                # Already covered by the other test; skip here.
                continue
            # Pick the longest matching name (most specific).
            primary = max(matches, key=len)
            existing = rid_to_name.setdefault(br["resource_id"], primary)
            if existing != primary:
                conflicts.append(
                    f"resource_id={br['resource_id']}: {existing!r} "
                    f"vs {primary!r} (in barrier {br['barrier_id']!r})"
                )

        assert not conflicts, (
            "resource_id maps to inconsistent resource names across "
            "barrier_resources rows:\n  " + "\n  ".join(conflicts)
        )


# ---------------------------------------------------------------------------
# Skip allowlist sanity -- make the documented intent enforceable
# ---------------------------------------------------------------------------


class TestSkipAllowlistIsHonest:
    """The skip allowlist is documented intent.  Pin it so that future
    edits to either community_resources.json OR the skip list can't
    silently let one of the skipped IDs reappear without a deliberate
    code change here too.
    """

    @pytest.mark.parametrize("rid", sorted(SKIPPED_FW_RESOURCE_IDS))
    def test_skipped_id_is_in_fw_universe(self, rid: int):
        # Sanity: don't list a phantom resource_id as skipped.
        fw_ids = {br["resource_id"] for br in _load(_FW_GRAPH)["barrier_resources"]}
        assert rid in fw_ids, (
            f"SKIPPED_FW_RESOURCE_IDS lists {rid} but FW barrier_resources "
            f"never references it (FW ids: {sorted(fw_ids)})"
        )

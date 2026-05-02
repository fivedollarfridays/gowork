"""Regression contract: the dual data tree must stay in sync.

Stage 1+2 left the project with TWO copies of the per-city seed data:

* ``backend/data/cities/<slug>/`` — used by the honestjobs seed loader and
  by every test fixture that imports a JSON path literally.
* ``data/cities/<slug>/`` — used by ``resolve_data_dir()`` (the resources +
  legacy seed path).

Stage 2 PR #105 fixed the divergence by syncing the FW resources.json into
both trees, but the asymmetric path resolution remained.  If anyone updates
ONE copy without the other, tests pass against the backend tree while the
runtime serves stale data from the root tree (or vice versa) — the exact
silent-failure mode that fails at 3am during a demo.

This test locks in the contract: every file under ``backend/data/cities/``
must have a byte-identical twin under root ``data/cities/`` (and vice
versa).  Failure here means someone updated one side and forgot the other.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

_BACKEND_ROOT = Path(__file__).resolve().parent.parent
_PROJECT_ROOT = _BACKEND_ROOT.parent
_BACKEND_CITIES = _BACKEND_ROOT / "data" / "cities"
_ROOT_CITIES = _PROJECT_ROOT / "data" / "cities"


def _md5(p: Path) -> str:
    return hashlib.md5(p.read_bytes()).hexdigest()


def _gather(base: Path) -> dict[str, str]:
    """Return ``{relative_posix_path: md5}`` for every file under base."""
    out: dict[str, str] = {}
    if not base.is_dir():
        return out
    for p in sorted(base.rglob("*")):
        if p.is_file():
            rel = p.relative_to(base).as_posix()
            out[rel] = _md5(p)
    return out


# Files that legitimately exist on ONE side of the tree.
# honestjobs_listings.json is loaded ONLY via backend/data/... by
# app.integrations.honestjobs.seed (its _DATA_DIR points at backend/data).
# Removing the backend/ copy would break the seed loader; adding to root
# would create a third source of truth.
_BACKEND_ONLY: set[str] = {
    # Per-city: each city's honestjobs is backend-tree only by design.
    "fort-worth/honestjobs_listings.json",
    "montgomery/honestjobs_listings.json",
}

# Files that legitimately exist on root /data/cities/ only.
# resolve_data_dir() (app.core.database) returns the city dir under root,
# so any seed file consumed via that resolver lives here.  The Montgomery
# directory has no resources.json today — its resources are seeded via
# the LEGACY fallback (career_centers.json + community_resources.json +
# training_programs.json + childcare_providers.json under root /data/).
_ROOT_ONLY: set[str] = {
    # FW employers directory consumed by the adapter registry.
    "fort-worth/employers.json",
    # Empty-dir placeholders (git can't track empty dirs).
    "fort-worth/.gitkeep",
    "montgomery/.gitkeep",
}

# Cities for which the per-city resources.json contract applies.
# Montgomery uses the legacy 4-file fallback under root /data/ (not a
# single resources.json), so it's intentionally excluded.
_RESOURCES_CITIES: tuple[str, ...] = ("fort-worth",)


class TestDualDataTreeSync:
    def test_backend_files_have_root_twins(self) -> None:
        """Every file in backend/data/cities/ must have a root twin
        with identical bytes — UNLESS it's an intentional backend-only
        file (see _BACKEND_ONLY allowlist).
        """
        backend_files = _gather(_BACKEND_CITIES)
        root_files = _gather(_ROOT_CITIES)
        drift: list[str] = []
        missing: list[str] = []

        for rel, md5 in backend_files.items():
            if rel in _BACKEND_ONLY:
                continue
            twin = root_files.get(rel)
            if twin is None:
                missing.append(rel)
            elif twin != md5:
                drift.append(rel)

        assert not missing, (
            f"Backend-tree files with no root twin (add to _BACKEND_ONLY "
            f"if intentional, otherwise sync to data/cities/): {missing}"
        )
        assert not drift, (
            f"Backend-tree files DIVERGED from their root twin -- one "
            f"side was edited without the other: {drift}"
        )

    def test_root_files_have_backend_twins(self) -> None:
        """Symmetric guard — the root tree must not grow files that the
        backend tree doesn't know about (would create asymmetric reads
        for the next person who edits resources.json).
        """
        backend_files = _gather(_BACKEND_CITIES)
        root_files = _gather(_ROOT_CITIES)
        orphans: list[str] = []

        for rel in root_files:
            if rel in _ROOT_ONLY:
                continue
            if rel not in backend_files:
                orphans.append(rel)

        assert not orphans, (
            f"Root-tree files with no backend twin (sync to "
            f"backend/data/cities/ or add to _ROOT_ONLY): {orphans}"
        )

    @pytest.mark.parametrize("slug", _RESOURCES_CITIES)
    def test_resources_json_in_both_trees(self, slug: str) -> None:
        """The single most demo-critical file MUST exist in both trees
        with identical content.  Stage 2 PR #105 was about this exact
        file -- this test prevents regressing it.
        """
        backend = _BACKEND_CITIES / slug / "resources.json"
        root = _ROOT_CITIES / slug / "resources.json"
        assert backend.exists(), f"missing backend twin: {backend}"
        assert root.exists(), f"missing root twin: {root}"
        assert _md5(backend) == _md5(root), (
            f"resources.json DRIFT for {slug} -- one tree was edited "
            f"without the other.  Sync them before merging."
        )

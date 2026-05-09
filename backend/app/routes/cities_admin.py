"""DFW cross-metro admin diagnostic summary (T25.7).

Single endpoint mounted under ``/api/admin/cities/...``:

* ``GET /summary`` — admin-gated read of per-city resource/employer/
  transit counts for the DFW metro (Fort Worth + Dallas), plus a
  ``dfw_total`` aggregate.

Charter integrity (S25 / T25.7)
-------------------------------
This route is **display-only**. No DB queries, no writes to matching
tables, no imports from :mod:`app.modules.matching`. Every count is
computed by reading the JSON seed files under
``data/cities/<slug>/`` via :func:`app.cities.config.load_city_config`
+ stdlib ``json``/``pathlib``.

The grep gate in T25.9 will assert that the matching module has zero
Dallas-specific references; this surface is the *consumer side* of
the same charter — it observes the seed corpus, not the matcher.

Response shape
--------------
::

    {
      "cities": [
        {
          "slug": "fort-worth",
          "name": "Fort Worth",
          "state": "TX",
          "resource_counts": {"social_service": 8, "career_center": 0, ...},
          "employer_count": 12,
          "fair_chance_count": 8,
          "fair_chance_pct": 0.6667,
          "transit_route_count": 14,
          "transit_stop_count": 42,
          "career_center_count": 1
        },
        { "slug": "dallas", ... }
      ],
      "dfw_total": { ...sum-of-fields, resource_counts merged by category... }
    }

``resource_counts`` is the union of categories observed across both
cities — a category present in only one city zero-fills in the other,
so the frontend can render parallel rows without re-keying the dict.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends

from app.cities.config import load_city_config
from app.core.auth_roles import require_role

# Project root resolved once at import. Mirrors the convention in
# :mod:`app.core.database` (``_PROJECT_ROOT = Path(__file__).resolve()
# .parent.parent.parent.parent``); ``data_dir`` in the city YAML is
# stored relative to the repo root, so we anchor at the same point.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# DFW metro = Fort Worth + Dallas (in that display order — FW left,
# Dallas right — to match the side-by-side admin layout).
_DFW_SLUGS: tuple[str, ...] = ("fort-worth", "dallas")

# Seed files we count. Each maps a JSON file under ``data/cities/<slug>/``
# to a count function that takes the parsed payload and returns an int.
_SCALAR_COUNT_FILES: tuple[tuple[str, str], ...] = (
    ("transit_routes.json", "transit_route_count"),
    ("transit_stops.json", "transit_stop_count"),
    ("career_centers.json", "career_center_count"),
)

router = APIRouter(prefix="/api/admin/cities", tags=["admin", "cities"])


def _load_json(path: Path) -> Any:
    """Read + parse a seed JSON file. Returns ``[]`` when missing.

    Missing-file tolerance keeps the diagnostic surface useful even
    if a city's seed corpus is partial — the admin page renders the
    available counts rather than 500ing.
    """
    if not path.is_file():
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _summarize_city(slug: str) -> dict[str, Any]:
    """Build the per-city summary payload from seed JSON files.

    No DB queries; every value derives from
    ``_PROJECT_ROOT / load_city_config(slug).data_dir``.
    """
    cfg = load_city_config(slug)
    data_dir = _PROJECT_ROOT / cfg.data_dir

    employers = _load_json(data_dir / "employers.json")
    employer_count = len(employers)
    fair_chance_count = sum(1 for e in employers if e.get("fair_chance"))
    fair_chance_pct = (
        round(fair_chance_count / employer_count, 4)
        if employer_count
        else 0.0
    )

    community_resources = _load_json(data_dir / "community_resources.json")
    resource_counts = dict(
        Counter(r.get("category", "") for r in community_resources)
    )

    summary: dict[str, Any] = {
        "slug": slug,
        "name": cfg.name,
        "state": cfg.state,
        "resource_counts": resource_counts,
        "employer_count": employer_count,
        "fair_chance_count": fair_chance_count,
        "fair_chance_pct": fair_chance_pct,
    }
    for filename, key in _SCALAR_COUNT_FILES:
        summary[key] = len(_load_json(data_dir / filename))
    return summary


def _zero_fill_resource_counts(
    cities: list[dict[str, Any]],
) -> None:
    """In-place: ensure every city dict has the union of categories.

    Categories present in only one city zero-fill in the other so the
    frontend can render parallel rows without re-keying the dict.
    """
    union: set[str] = set()
    for city in cities:
        union.update(city["resource_counts"].keys())
    for city in cities:
        for cat in union:
            city["resource_counts"].setdefault(cat, 0)


def _aggregate_dfw_total(cities: list[dict[str, Any]]) -> dict[str, Any]:
    """Sum per-field counts across cities; merge resource_counts by category."""
    total: dict[str, Any] = {
        "employer_count": 0,
        "fair_chance_count": 0,
        "transit_route_count": 0,
        "transit_stop_count": 0,
        "career_center_count": 0,
    }
    merged: Counter[str] = Counter()
    for city in cities:
        for key in (
            "employer_count",
            "fair_chance_count",
            "transit_route_count",
            "transit_stop_count",
            "career_center_count",
        ):
            total[key] += city[key]
        merged.update(city["resource_counts"])
    total["resource_counts"] = dict(merged)
    total["fair_chance_pct"] = (
        round(total["fair_chance_count"] / total["employer_count"], 4)
        if total["employer_count"]
        else 0.0
    )
    return total


@router.get("/summary")
async def get_dfw_summary(
    _account: dict = Depends(require_role("admin")),
) -> dict[str, Any]:
    """Return the side-by-side DFW metro diagnostic summary.

    Read-only. Counts come exclusively from JSON seed files — no DB
    queries, no matching-engine imports. Any future cross-metro match
    feature must justify the design change before this surface is
    repurposed; the admin page header carries the same warning copy.
    """
    cities = [_summarize_city(slug) for slug in _DFW_SLUGS]
    _zero_fill_resource_counts(cities)
    return {
        "cities": cities,
        "dfw_total": _aggregate_dfw_total(cities),
    }


__all__ = ["router"]

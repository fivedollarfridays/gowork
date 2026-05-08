"""Tests for scripts/import_gtfs.py — GTFS to canonical FW transit JSON.

Fixture: scripts/__tests__/fixtures/mini_dart_gtfs/ (3 routes, 8 stops).
"""

from __future__ import annotations

import importlib.util
import json
import sys
import zipfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "mini_dart_gtfs"

# Load scripts/import_gtfs.py as a module without polluting sys.path globally.
_SPEC = importlib.util.spec_from_file_location(
    "import_gtfs", SCRIPTS_DIR / "import_gtfs.py"
)
import_gtfs = importlib.util.module_from_spec(_SPEC)  # type: ignore[arg-type]
sys.modules["import_gtfs"] = import_gtfs
_SPEC.loader.exec_module(import_gtfs)  # type: ignore[union-attr]


GTFS_FILES = (
    "calendar.txt",
    "routes.txt",
    "trips.txt",
    "stops.txt",
    "stop_times.txt",
)


def _build_gtfs_zip(tmp_path: Path) -> Path:
    """Pack the fixture txt files into a real zip for the importer."""
    zip_path = tmp_path / "dart_gtfs.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for name in GTFS_FILES:
            src = FIXTURE_DIR / name
            zf.writestr(name, src.read_text(encoding="utf-8"))
    return zip_path


@pytest.fixture()
def gtfs_zip(tmp_path: Path) -> Path:
    return _build_gtfs_zip(tmp_path)


@pytest.fixture()
def out_dir(tmp_path: Path) -> Path:
    out = tmp_path / "data" / "cities" / "testcity"
    out.mkdir(parents=True, exist_ok=True)
    return out


def _run_importer(zip_path: Path, city: str, data_root: Path) -> tuple[Path, Path]:
    routes_path, stops_path = import_gtfs.import_gtfs(
        gtfs_zip=zip_path, city=city, data_root=data_root
    )
    return routes_path, stops_path


# ---------------------------------------------------------------------------
# Cycle 1 — routes count + schema
# ---------------------------------------------------------------------------


def test_routes_output_count_matches_fixture(gtfs_zip: Path, tmp_path: Path) -> None:
    routes_path, _ = _run_importer(gtfs_zip, "testcity", tmp_path / "data")
    routes = json.loads(routes_path.read_text())
    assert len(routes) == 3


def test_routes_schema_matches_fw_canonical(gtfs_zip: Path, tmp_path: Path) -> None:
    routes_path, _ = _run_importer(gtfs_zip, "testcity", tmp_path / "data")
    routes = json.loads(routes_path.read_text())
    expected_keys = {
        "route_number",
        "route_name",
        "weekday_start",
        "weekday_end",
        "saturday",
        "sunday",
    }
    for row in routes:
        assert set(row.keys()) == expected_keys, row
        assert isinstance(row["route_number"], int)
        assert isinstance(row["route_name"], str)
        assert isinstance(row["weekday_start"], str)
        assert isinstance(row["weekday_end"], str)
        assert isinstance(row["saturday"], bool)
        assert isinstance(row["sunday"], bool)


def test_routes_output_path_uses_city_slug(gtfs_zip: Path, tmp_path: Path) -> None:
    routes_path, stops_path = _run_importer(gtfs_zip, "dallas", tmp_path / "data")
    assert routes_path == tmp_path / "data" / "cities" / "dallas" / "transit_routes.json"
    assert stops_path == tmp_path / "data" / "cities" / "dallas" / "transit_stops.json"


# ---------------------------------------------------------------------------
# Cycle 2 — stops count + ordering + schema
# ---------------------------------------------------------------------------


def test_stops_output_count_matches_fixture(gtfs_zip: Path, tmp_path: Path) -> None:
    _, stops_path = _run_importer(gtfs_zip, "testcity", tmp_path / "data")
    stops = json.loads(stops_path.read_text())
    # R1: S1,S2,S3 (3) + R2: S4,S5 (2) + R3: S6,S7,S8 (3) = 8
    assert len(stops) == 8


def test_stops_schema_matches_fw_canonical(gtfs_zip: Path, tmp_path: Path) -> None:
    _, stops_path = _run_importer(gtfs_zip, "testcity", tmp_path / "data")
    stops = json.loads(stops_path.read_text())
    expected_keys = {"route_id", "stop_name", "lat", "lng", "sequence"}
    for row in stops:
        assert set(row.keys()) == expected_keys, row
        assert isinstance(row["route_id"], int)
        assert isinstance(row["stop_name"], str)
        assert isinstance(row["lat"], float)
        assert isinstance(row["lng"], float)
        assert isinstance(row["sequence"], int)


def test_stops_sequence_preserved_per_route(gtfs_zip: Path, tmp_path: Path) -> None:
    _, stops_path = _run_importer(gtfs_zip, "testcity", tmp_path / "data")
    stops = json.loads(stops_path.read_text())
    # Group by route_id and confirm sequence is monotonically increasing 1..N.
    by_route: dict[int, list[dict]] = {}
    for row in stops:
        by_route.setdefault(row["route_id"], []).append(row)
    for route_id, rows in by_route.items():
        seqs = [r["sequence"] for r in rows]
        assert seqs == sorted(seqs), f"route {route_id} stops not sorted by seq"
        assert seqs == list(range(1, len(seqs) + 1)), (
            f"route {route_id} sequence not 1..N"
        )


def test_stops_lat_lng_rounded_to_4_decimals(gtfs_zip: Path, tmp_path: Path) -> None:
    _, stops_path = _run_importer(gtfs_zip, "testcity", tmp_path / "data")
    stops = json.loads(stops_path.read_text())
    for row in stops:
        # round to 4 decimals — never more precision than 4 places after the point.
        lat_str = repr(row["lat"])
        lng_str = repr(row["lng"])
        for v in (lat_str, lng_str):
            if "." in v:
                frac = v.split(".", 1)[1]
                assert len(frac) <= 4, f"value {v} exceeds 4 decimal places"


# ---------------------------------------------------------------------------
# Cycle 3 — weekday window derivation
# ---------------------------------------------------------------------------


def _route_by_number(routes: list[dict], number: int) -> dict:
    for row in routes:
        if row["route_number"] == number:
            return row
    raise AssertionError(f"route {number} not in output")


def test_weekday_window_derived_from_stop_times_min_max(
    gtfs_zip: Path, tmp_path: Path
) -> None:
    routes_path, _ = _run_importer(gtfs_zip, "testcity", tmp_path / "data")
    routes = json.loads(routes_path.read_text())
    # Route 1 (R1) has WKDY trips T1A (05:30-05:40) and T1B (21:00-21:10).
    # min departure = 05:30, max arrival = 21:10.
    r1 = _route_by_number(routes, 1)
    assert r1["weekday_start"] == "05:30"
    assert r1["weekday_end"] == "21:10"


def test_weekday_window_for_route_with_only_weekday_service(
    gtfs_zip: Path, tmp_path: Path
) -> None:
    routes_path, _ = _run_importer(gtfs_zip, "testcity", tmp_path / "data")
    routes = json.loads(routes_path.read_text())
    # Route 3 (R3) WKDY trip T3A: 07:15-07:35.
    r3 = _route_by_number(routes, 3)
    assert r3["weekday_start"] == "07:15"
    assert r3["weekday_end"] == "07:35"


# ---------------------------------------------------------------------------
# Cycle 4 — saturday / sunday flags
# ---------------------------------------------------------------------------


def test_weekday_only_route_has_no_weekend_service(
    gtfs_zip: Path, tmp_path: Path
) -> None:
    routes_path, _ = _run_importer(gtfs_zip, "testcity", tmp_path / "data")
    routes = json.loads(routes_path.read_text())
    r1 = _route_by_number(routes, 1)
    assert r1["saturday"] is False
    assert r1["sunday"] is False


def test_daily_route_has_weekend_service(gtfs_zip: Path, tmp_path: Path) -> None:
    routes_path, _ = _run_importer(gtfs_zip, "testcity", tmp_path / "data")
    routes = json.loads(routes_path.read_text())
    # Route 2 (R2) primary service is DAILY (tie-break alpha) — sat=sun=True.
    r2 = _route_by_number(routes, 2)
    assert r2["saturday"] is True
    assert r2["sunday"] is True


# ---------------------------------------------------------------------------
# Cycle 5 — idempotency (byte-identical JSON across two runs)
# ---------------------------------------------------------------------------


def test_idempotent_byte_identical_across_runs(
    gtfs_zip: Path, tmp_path: Path
) -> None:
    data_root = tmp_path / "data"
    routes_path, stops_path = _run_importer(gtfs_zip, "testcity", data_root)
    routes_first = routes_path.read_bytes()
    stops_first = stops_path.read_bytes()

    # Second run on the SAME zip + SAME city — must produce byte-identical output.
    _run_importer(gtfs_zip, "testcity", data_root)
    routes_second = routes_path.read_bytes()
    stops_second = stops_path.read_bytes()

    assert routes_first == routes_second, "routes JSON not byte-identical"
    assert stops_first == stops_second, "stops JSON not byte-identical"


def test_output_uses_sort_keys_indent_2(gtfs_zip: Path, tmp_path: Path) -> None:
    routes_path, stops_path = _run_importer(
        gtfs_zip, "testcity", tmp_path / "data"
    )
    # If sort_keys=True with indent=2 was used, re-serializing the parsed JSON
    # with those same options must produce the same bytes (modulo trailing newline).
    for path in (routes_path, stops_path):
        raw = path.read_text()
        parsed = json.loads(raw)
        re_dumped = json.dumps(parsed, sort_keys=True, indent=2)
        assert raw.rstrip("\n") == re_dumped.rstrip("\n"), (
            f"{path.name} not deterministic-formatted"
        )

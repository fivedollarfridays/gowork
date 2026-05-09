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


# ---------------------------------------------------------------------------
# Cycle 6 — calendar_dates.txt support (DART pattern)
# ---------------------------------------------------------------------------
#
# Some agencies (DART) put the bulk of operating days in calendar_dates.txt
# (date-by-date enumeration) rather than the repeating M-F pattern in
# calendar.txt. The importer must derive day-of-week flags from the dates
# for service_ids absent from calendar.txt. Service_ids in calendar.txt
# take precedence (calendar.txt is the authoritative repeating pattern).


# Calendar with ONLY weekend services (mirrors DART's pattern: weekday
# service lives in calendar_dates.txt, calendar.txt covers Sat/Sun only).
_CALDATES_CALENDAR_TXT = (
    "service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date\n"
    "SAT_ONLY,0,0,0,0,0,1,0,20260101,20261231\n"
    "SUN_ONLY,0,0,0,0,0,0,1,20260101,20261231\n"
)
# Mon-Fri operating dates for a "WKDY_DATES" service_id (5 weekdays in a
# row → derives M-F flags). 20260511 = Mon, 20260512 = Tue, etc.
_CALDATES_DATES_TXT = (
    "service_id,date,exception_type\n"
    "WKDY_DATES,20260511,1\n"
    "WKDY_DATES,20260512,1\n"
    "WKDY_DATES,20260513,1\n"
    "WKDY_DATES,20260514,1\n"
    "WKDY_DATES,20260515,1\n"
)
_CALDATES_ROUTES_TXT = (
    "route_id,route_short_name,route_long_name\n"
    "RX,7,WEEKDAY_VIA_CALENDAR_DATES\n"
)
_CALDATES_TRIPS_TXT = (
    "trip_id,route_id,service_id\n"
    "RX_T1,RX,WKDY_DATES\n"
    "RX_T2,RX,SAT_ONLY\n"
)
_CALDATES_STOPS_TXT = (
    "stop_id,stop_name,stop_lat,stop_lon\n"
    "S1,First Stop,32.7510,-97.3260\n"
    "S2,Second Stop,32.7520,-97.3270\n"
)
_CALDATES_STOP_TIMES_TXT = (
    "trip_id,arrival_time,departure_time,stop_id,stop_sequence\n"
    "RX_T1,06:00:00,06:00:00,S1,1\n"
    "RX_T1,21:30:00,21:30:00,S2,2\n"
    "RX_T2,07:00:00,07:00:00,S1,1\n"
    "RX_T2,18:00:00,18:00:00,S2,2\n"
)


@pytest.fixture()
def gtfs_zip_caldates(tmp_path: Path) -> Path:
    """Pack a GTFS bundle that uses calendar_dates.txt for weekday service."""
    zip_path = tmp_path / "caldates_gtfs.zip"
    files = {
        "calendar.txt": _CALDATES_CALENDAR_TXT,
        "calendar_dates.txt": _CALDATES_DATES_TXT,
        "routes.txt": _CALDATES_ROUTES_TXT,
        "trips.txt": _CALDATES_TRIPS_TXT,
        "stops.txt": _CALDATES_STOPS_TXT,
        "stop_times.txt": _CALDATES_STOP_TIMES_TXT,
    }
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, body in files.items():
            zf.writestr(name, body)
    return zip_path


def test_calendar_dates_drives_weekday_window(
    gtfs_zip_caldates: Path, tmp_path: Path
) -> None:
    """Route uses a service_id present only in calendar_dates.txt — its
    weekday window must derive from those dates' stop_times, NOT come back
    "00:00"-"00:00". This is the DART pattern that motivated the support."""
    routes_path, _ = _run_importer(gtfs_zip_caldates, "calcity", tmp_path / "data")
    routes = json.loads(routes_path.read_text())
    rx = _route_by_number(routes, 7)
    assert rx["weekday_start"] == "06:00", (
        f"weekday_start should derive from RX_T1 stop_times min, got {rx}"
    )
    assert rx["weekday_end"] == "21:30", (
        f"weekday_end should derive from RX_T1 stop_times max, got {rx}"
    )


def test_calendar_dates_route_runs_saturday_via_separate_service(
    gtfs_zip_caldates: Path, tmp_path: Path
) -> None:
    """Same route also has a SAT_ONLY trip — sat must be True even though
    SAT_ONLY is a different service_id from the weekday service. Mirrors
    the bug surfaced on live DART: sat/sun cannot be read from a single
    "primary" service; must aggregate across all service_ids the route uses.
    """
    routes_path, _ = _run_importer(gtfs_zip_caldates, "calcity", tmp_path / "data")
    routes = json.loads(routes_path.read_text())
    rx = _route_by_number(routes, 7)
    assert rx["saturday"] is True, (
        f"saturday should aggregate across all service_ids, got {rx}"
    )
    assert rx["sunday"] is False, (
        f"sunday should be False (no service runs Sunday), got {rx}"
    )


def test_calendar_txt_takes_precedence_over_calendar_dates(tmp_path: Path) -> None:
    """If a service_id is in BOTH calendar.txt and calendar_dates.txt, the
    calendar.txt entry is authoritative. This pin prevents accidental
    overrides when an agency uses calendar_dates.txt for exceptions only."""
    zip_path = tmp_path / "precedence.zip"
    cal_txt = (
        "service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date\n"
        # SHARED is M-W only per calendar.txt:
        "SHARED,1,1,1,0,0,0,0,20260101,20261231\n"
    )
    # calendar_dates.txt would suggest Thursday + Friday — but calendar.txt wins.
    cal_dates = (
        "service_id,date,exception_type\n"
        "SHARED,20260514,1\n"  # Thursday
        "SHARED,20260515,1\n"  # Friday
    )
    routes_txt = (
        "route_id,route_short_name,route_long_name\n"
        "PR,11,PRECEDENCE\n"
    )
    trips_txt = "trip_id,route_id,service_id\nPR_T1,PR,SHARED\n"
    stops_txt = "stop_id,stop_name,stop_lat,stop_lon\nS1,A,32.0,-97.0\nS2,B,32.1,-97.1\n"
    stop_times_txt = (
        "trip_id,arrival_time,departure_time,stop_id,stop_sequence\n"
        "PR_T1,07:00:00,07:00:00,S1,1\n"
        "PR_T1,17:00:00,17:00:00,S2,2\n"
    )
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, body in {
            "calendar.txt": cal_txt,
            "calendar_dates.txt": cal_dates,
            "routes.txt": routes_txt,
            "trips.txt": trips_txt,
            "stops.txt": stops_txt,
            "stop_times.txt": stop_times_txt,
        }.items():
            zf.writestr(name, body)
    routes_path, _ = _run_importer(zip_path, "prcity", tmp_path / "data")
    routes = json.loads(routes_path.read_text())
    pr = _route_by_number(routes, 11)
    # calendar.txt says SHARED is M-W only. weekday window should derive from
    # the route's stop_times under SHARED (not from any synthetic calendar_dates
    # extension that would say "also Thu+Fri").
    assert pr["weekday_start"] == "07:00"
    assert pr["weekday_end"] == "17:00"
    # SHARED has saturday=0 and sunday=0 in calendar.txt, so flags are False
    # even though calendar_dates.txt could be read as adding more days.
    assert pr["saturday"] is False
    assert pr["sunday"] is False

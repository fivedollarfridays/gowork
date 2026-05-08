"""GTFS -> canonical FW transit JSON importer.

Reusable boundary between any GTFS feed (DART, Houston METRO, etc.) and the
two canonical files consumed by the per-city transit loader:

    data/cities/<slug>/transit_routes.json
    data/cities/<slug>/transit_stops.json

Shapes (must match Fort Worth reference exactly):

    transit_routes.json -> [
        {"route_number": int, "route_name": str,
         "weekday_start": "HH:MM", "weekday_end": "HH:MM",
         "saturday": bool, "sunday": bool}, ...
    ]

    transit_stops.json -> [
        {"route_id": int, "stop_name": str,
         "lat": float, "lng": float, "sequence": int}, ...
    ]

Stdlib only (zipfile, csv, json, argparse, pathlib). Idempotent: re-running
on the same GTFS bundle yields byte-identical JSON.

Usage:
    python scripts/import_gtfs.py --gtfs-zip path/to/feed.zip --city dallas
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import sys
import zipfile
from pathlib import Path
from typing import Iterable

# Allow `python scripts/import_gtfs.py` invocation without a package shim.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from import_gtfs_calendar import (  # noqa: E402
    derive_weekday_window,
    index_calendar,
    select_primary_service,
)
from import_gtfs_stops import (  # noqa: E402
    index_stop_times_by_trip,
    index_trips_by_route,
    ordered_stops_for_route,
    route_name_from_row,
    route_number_from_row,
)

GTFS_REQUIRED_FILES = (
    "calendar.txt",
    "routes.txt",
    "trips.txt",
    "stops.txt",
    "stop_times.txt",
)
LATLNG_PRECISION = 4


# ---------------------------------------------------------------------------
# GTFS table reader
# ---------------------------------------------------------------------------


def read_gtfs_table(zf: zipfile.ZipFile, name: str) -> list[dict]:
    with zf.open(name) as raw:
        text = io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")
        return list(csv.DictReader(text))


def load_gtfs_tables(gtfs_zip: Path) -> dict[str, list[dict]]:
    if not gtfs_zip.exists():
        raise FileNotFoundError(f"GTFS zip not found: {gtfs_zip}")
    tables: dict[str, list[dict]] = {}
    with zipfile.ZipFile(gtfs_zip, "r") as zf:
        names = set(zf.namelist())
        for required in GTFS_REQUIRED_FILES:
            if required not in names:
                raise ValueError(f"GTFS zip missing required file: {required}")
            tables[required] = read_gtfs_table(zf, required)
    return tables


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------


def _build_route_row(
    row: dict, idx: int, trips: list[dict], stop_times: list[dict],
    cal_index: dict[str, dict],
) -> dict:
    route_id = row["route_id"]
    primary_sid = select_primary_service(route_id, trips, cal_index)
    sat, sun = False, False
    if primary_sid is not None:
        cal = cal_index[primary_sid]
        sat = cal.get("saturday") == "1"
        sun = cal.get("sunday") == "1"
    wkday_start, wkday_end = derive_weekday_window(
        route_id, trips, stop_times, cal_index
    )
    return {
        "route_number": route_number_from_row(row, idx),
        "route_name": route_name_from_row(row),
        "weekday_start": wkday_start,
        "weekday_end": wkday_end,
        "saturday": sat,
        "sunday": sun,
    }


def build_routes(tables: dict[str, list[dict]]) -> list[dict]:
    cal_index = index_calendar(tables["calendar.txt"])
    trips = tables["trips.txt"]
    stop_times = tables["stop_times.txt"]
    out = [
        _build_route_row(row, idx, trips, stop_times, cal_index)
        for idx, row in enumerate(tables["routes.txt"], start=1)
    ]
    out.sort(key=lambda r: (r["route_number"], r["route_name"]))
    return out


def _build_stop_row(route_id_int: int, stop: dict, seq: int) -> dict:
    return {
        "route_id": route_id_int,
        "stop_name": (stop.get("stop_name") or "").strip(),
        "lat": round(float(stop["stop_lat"]), LATLNG_PRECISION),
        "lng": round(float(stop["stop_lon"]), LATLNG_PRECISION),
        "sequence": seq,
    }


def build_stops(tables: dict[str, list[dict]]) -> list[dict]:
    routes_tbl = tables["routes.txt"]
    stop_lookup = {row["stop_id"]: row for row in tables["stops.txt"]}
    trips_by_route = index_trips_by_route(tables["trips.txt"])
    stop_times_by_trip = index_stop_times_by_trip(tables["stop_times.txt"])

    out: list[dict] = []
    for idx, route_row in enumerate(routes_tbl, start=1):
        route_id_int = route_number_from_row(route_row, idx)
        ordered = ordered_stops_for_route(
            route_row["route_id"], trips_by_route, stop_times_by_trip
        )
        for seq, stop_id in enumerate(ordered, start=1):
            stop = stop_lookup.get(stop_id)
            if stop is not None:
                out.append(_build_stop_row(route_id_int, stop, seq))
    out.sort(key=lambda s: (s["route_id"], s["sequence"]))
    return out


# ---------------------------------------------------------------------------
# Output writer
# ---------------------------------------------------------------------------


def _serialize(payload: list[dict]) -> str:
    return json.dumps(payload, sort_keys=True, indent=2) + "\n"


def write_outputs(
    routes: list[dict], stops: list[dict], data_root: Path, city: str
) -> tuple[Path, Path]:
    out_dir = data_root / "cities" / city
    out_dir.mkdir(parents=True, exist_ok=True)
    routes_path = out_dir / "transit_routes.json"
    stops_path = out_dir / "transit_stops.json"
    routes_path.write_text(_serialize(routes), encoding="utf-8")
    stops_path.write_text(_serialize(stops), encoding="utf-8")
    return routes_path, stops_path


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def import_gtfs(
    gtfs_zip: Path, city: str, data_root: Path
) -> tuple[Path, Path]:
    """Import a GTFS zip and write canonical JSON for `city`. Returns paths."""
    tables = load_gtfs_tables(gtfs_zip)
    return write_outputs(build_routes(tables), build_stops(tables), data_root, city)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="import_gtfs",
        description="Import a GTFS zip into canonical FW transit JSON.",
    )
    parser.add_argument("--gtfs-zip", required=True, type=Path)
    parser.add_argument("--city", required=True)
    parser.add_argument("--data-root", type=Path, default=Path("data"))
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(list(argv) if argv is not None else None)
    routes_path, stops_path = import_gtfs(
        gtfs_zip=args.gtfs_zip, city=args.city, data_root=args.data_root
    )
    print(f"Wrote {routes_path}")
    print(f"Wrote {stops_path}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

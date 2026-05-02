"""Backfill geocoding for Fort Worth resources + jobs.

Updates two artifacts in place: the seed JSON
(``backend/data/cities/fort-worth/resources.json``) and the
``job_listings`` table in the runtime SQLite DB. Idempotent — rows
that already have ``lat`` AND ``lng`` are skipped. Rows missing an
address / location are skipped (Mapbox needs something to lock onto).

Rate-limited (default 1.0 s) to stay polite on Mapbox's free tier.
``--rate 0`` for tests. Run via ``python -m
scripts.backfill_geocode_fw_data``.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Optional

from app.integrations.mapbox.geocoder import geocode_address

_logger = logging.getLogger(__name__)

_DEFAULT_RATE_SECONDS = 1.0


@dataclass
class BackfillResult:
    """Per-source counters returned by the backfill loops."""

    geocoded: int = 0
    failed: int = 0
    skipped: int = 0


# ---------- Pure decision helpers --------------------------------------


def needs_geocode(row: dict[str, Any]) -> bool:
    """Return True iff *row* has an address but no coordinates yet."""
    if not row.get("address"):
        return False
    return row.get("lat") is None or row.get("lng") is None


def _job_needs_geocode(row: tuple[Any, ...]) -> bool:
    """Tuple form: (id, location, lat, lng) — used by the DB loop."""
    _id, location, lat, lng = row
    if not location:
        return False
    return lat is None or lng is None


# ---------- Resources JSON loop ----------------------------------------


async def backfill_resources_file(
    path: str, rate_limit_seconds: float = _DEFAULT_RATE_SECONDS,
) -> BackfillResult:
    """Geocode every row in *path* that needs it; persist back in-place."""
    file_path = Path(path)
    resources: list[dict[str, Any]] = json.loads(
        file_path.read_text(encoding="utf-8"),
    )
    result = BackfillResult()

    for resource in resources:
        if not needs_geocode(resource):
            result.skipped += 1
            continue
        coords = await geocode_address(resource["address"])
        if coords is None:
            result.failed += 1
            _logger.warning(
                "geocode failed for resource %r at %r",
                resource.get("name"), resource.get("address"),
            )
        else:
            resource["lat"], resource["lng"] = coords
            result.geocoded += 1
        if rate_limit_seconds > 0:
            await asyncio.sleep(rate_limit_seconds)

    file_path.write_text(
        json.dumps(resources, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return result


# ---------- Jobs DB loop -----------------------------------------------


def _select_jobs(con: sqlite3.Connection) -> list[tuple[Any, ...]]:
    """All rows; lets us count skipped without an extra query."""
    return con.execute(
        "SELECT id, location, lat, lng FROM job_listings",
    ).fetchall()


def _update_job_coords(
    con: sqlite3.Connection, job_id: int, lat: float, lng: float,
) -> None:
    con.execute(
        "UPDATE job_listings SET lat = ?, lng = ? WHERE id = ?",
        (lat, lng, job_id),
    )


async def backfill_jobs_db(
    db_path: str, rate_limit_seconds: float = _DEFAULT_RATE_SECONDS,
) -> BackfillResult:
    """Geocode every ``job_listings`` row that needs it; UPDATE in place."""
    con = sqlite3.connect(db_path)
    try:
        rows = _select_jobs(con)
        result = BackfillResult()
        for row in rows:
            if not _job_needs_geocode(row):
                result.skipped += 1
                continue
            job_id, location, _lat, _lng = row
            coords = await geocode_address(location)
            if coords is None:
                result.failed += 1
                _logger.warning(
                    "geocode failed for job id=%d location=%r",
                    job_id, location,
                )
            else:
                _update_job_coords(con, job_id, coords[0], coords[1])
                result.geocoded += 1
            if rate_limit_seconds > 0:
                await asyncio.sleep(rate_limit_seconds)
        con.commit()
        return result
    finally:
        con.close()


# ---------- CLI entrypoint ---------------------------------------------


def _parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Backfill geocoding for FW resources + jobs.",
    )
    parser.add_argument(
        "--resources-file",
        default="backend/data/cities/fort-worth/resources.json",
    )
    parser.add_argument("--db", default="backend/montgowork.db")
    parser.add_argument(
        "--rate", type=float, default=_DEFAULT_RATE_SECONDS,
        help="Seconds between API calls (default 1.0).",
    )
    parser.add_argument(
        "--skip-resources", action="store_true",
        help="Skip the resources.json pass.",
    )
    parser.add_argument(
        "--skip-jobs", action="store_true",
        help="Skip the job_listings DB pass.",
    )
    return parser.parse_args(list(argv) if argv is not None else None)


async def _run(args: argparse.Namespace) -> int:
    """Run the configured backfills, print a summary, return exit code."""
    if not args.skip_resources:
        print(f"resources.json -> {args.resources_file}")
        res = await backfill_resources_file(args.resources_file, args.rate)
        print(
            f"  geocoded={res.geocoded} failed={res.failed} "
            f"skipped={res.skipped}",
        )
    if not args.skip_jobs:
        print(f"job_listings -> {args.db}")
        jobs = await backfill_jobs_db(args.db, args.rate)
        print(
            f"  geocoded={jobs.geocoded} failed={jobs.failed} "
            f"skipped={jobs.skipped}",
        )
    return 0


def main(argv: Optional[Iterable[str]] = None) -> int:  # pragma: no cover
    """Module-level entrypoint for ``python -m`` / shell invocation."""
    logging.basicConfig(level=logging.INFO)
    args = _parse_args(argv)
    return asyncio.run(_run(args))


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())

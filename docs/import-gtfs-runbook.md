# GTFS Importer Runbook

`scripts/import_gtfs.py` is the canonical GTFS → MontGoWork transit JSON
importer. This document covers fetching feeds, running the importer, expected
output shapes, and per-city sanity floors.

## What it does

Reads any standards-compliant GTFS zip and emits two files matching the
Fort Worth reference shape (the contract that the per-city transit loader
in `backend/app/cities/<city>/transit.py` consumes):

```
data/cities/<slug>/transit_routes.json
data/cities/<slug>/transit_stops.json
```

## Output shapes (load-bearing — do not change)

`transit_routes.json`:

```json
[
  {
    "route_number": 1,
    "route_name": "Vickery",
    "weekday_start": "05:30",
    "weekday_end":   "21:00",
    "saturday":      true,
    "sunday":        false
  }
]
```

`transit_stops.json`:

```json
[
  {
    "route_id":  1,
    "stop_name": "Central Station (downtown)",
    "lat":       32.7510,
    "lng":      -97.3260,
    "sequence":  1
  }
]
```

Notes:
- `weekday_start` / `weekday_end` are derived from `stop_times.txt` MIN/MAX
  across trips whose `service_id` is enabled on at least one Mon-Fri day.
- `saturday` / `sunday` are read from `calendar.txt` for the route's
  *primary* `service_id` (most trips for that route; tie-broken alphabetically).
- `lat` / `lng` are rounded to 4 decimal places.
- `sequence` is the de-duplicated stop visit order across all trips on the
  route — each stop appears once per route, in canonical visit order.
- Output is JSON-serialized with `sort_keys=True, indent=2` plus trailing
  newline. Re-running on the same GTFS zip produces byte-identical output.

## How to invoke

```bash
# From repo root:
python3 scripts/import_gtfs.py \
    --gtfs-zip path/to/dart_gtfs.zip \
    --city dallas \
    [--data-root data]
```

The importer is stdlib-only (`zipfile`, `csv`, `json`, `argparse`, `pathlib`)
— no external dependencies, no virtualenv needed.

## Where to fetch each city's GTFS feed

### Dallas — DART (Dallas Area Rapid Transit)

- Operator: <https://www.dart.org>
- Open-data portal: <https://www.dart.org/about/about-dart/fixed-route-schedule>
  (look for the "GTFS" or "Developer Resources" link)
- License: DART makes the GTFS feed publicly available. Attribution
  appreciated. Confirm current terms on their developer page before
  shipping anything user-facing.
- Sanity floor (live feed): >= 80 routes, >= 1000 stops.

### Fort Worth — Trinity Metro

- Operator: <https://www.ridetrm.org>
- The current `data/cities/fort-worth/transit_*.json` files are *hand-curated*
  pre-importer; do not regenerate from the live feed without ops sign-off.
- Sanity floor: 14 routes, ~42 stops (the existing seed).

### Houston (future) — METRO

- Operator: <https://www.ridemetro.org>
- Open-data portal:
  <https://www.ridemetro.org/about/business-center/developer-resources>
- License: METRO publishes GTFS under their developer-resources terms.
- Expected sanity floor (live feed): >= 90 routes, >= 9000 stops.

### Adding more cities

Any GTFS-compliant feed will work. The importer requires these five files
inside the zip: `calendar.txt`, `routes.txt`, `trips.txt`, `stops.txt`,
`stop_times.txt`. Optional GTFS files (`shapes.txt`, `frequencies.txt`,
`calendar_dates.txt`) are ignored.

## Per-city sanity floors

After running the importer, verify the output:

```bash
python3 -c "import json,sys; \
    r=json.load(open('data/cities/$CITY/transit_routes.json')); \
    s=json.load(open('data/cities/$CITY/transit_stops.json')); \
    print(f'routes={len(r)} stops={len(s)}')"
```

| City        | Floor (routes) | Floor (stops) | Source                  |
| ----------- | -------------- | ------------- | ----------------------- |
| Fort Worth  | 14             | 42            | hand-curated seed       |
| Dallas      | 80             | 1000          | live DART GTFS (target) |
| Dallas      | 20             | 250           | demo seed (T25.5 ship)  |
| Houston     | 90             | 9000          | live METRO GTFS (future)|

## Demo-seed caveat (Sprint 25 / T25.5)

The Dallas seed shipped in T25.5 is **synthetic, not from the live DART
GTFS feed**. The Sprint 25 environment has restricted network access
(dart.org is not reachable), so we generated a representative dataset
that exercises the full importer code path:

- 4 light-rail lines (Red, Blue, Green, Orange) with real station names
  and approximate published latitude/longitude for the major shared
  downtown stations (Union, West End, Akard, St Paul, Pearl, Cityplace,
  Mockingbird, Lovers Lane, etc.).
- 23 representative DART bus routes using real DART route numbers
  (1, 19, 21, 26, 36, 51, 60, 161, 183, 240, 282, 360, 401, 408, 466,
  521, 528, 549, 595, 700, 702, 703, 704). Stop coordinates are
  approximated.
- Output: 27 routes, 303 stops.

**Production replacement plan:** when network access to dart.org is
available, run:

```bash
curl -L -o /tmp/dart.zip https://www.dart.org/.../google_transit.zip
python3 scripts/import_gtfs.py --gtfs-zip /tmp/dart.zip --city dallas
git diff data/cities/dallas/transit_*.json   # review the swap
```

The importer itself is production-ready. Only the seed payload needs to
be replaced; no code changes are required to swap the synthetic seed for
the real DART feed.

## Edge cases / GTFS quirks

- **Times >= 24:00.** GTFS allows times like `25:30:00` to express
  next-day service. The importer wraps these with `% 24` so output is
  always `HH:MM` in the 00-23 range.
- **Routes with no weekday service.** If a route has zero trips on any
  weekday `service_id`, `weekday_start` and `weekday_end` are both
  `"00:00"` — the row is still emitted so the route count is preserved.
- **Routes with no `route_short_name`.** Falls back to digits parsed from
  `route_id`, then to a stable per-position index. Still produces an
  integer `route_number`.
- **Mismatched `stop_id` references.** Stop_times rows that reference an
  unknown `stop_id` are silently dropped. Run a GTFS validator upstream
  if this matters.
- **`calendar_dates.txt` overrides.** Not consumed in the current
  importer. If a feed expresses service primarily through
  `calendar_dates.txt` exceptions, the derived weekday window may be
  incomplete; revisit when we add a city that depends on it.

## Architecture

The importer is decomposed across three small modules, all under the
project's per-file architecture limits:

```
scripts/import_gtfs.py            # CLI + orchestrator + I/O
scripts/import_gtfs_calendar.py   # service_id selection + weekday window
scripts/import_gtfs_stops.py      # stop ordering, route number/name
```

Tests live in `scripts/__tests__/test_import_gtfs.py` and feed a
`scripts/__tests__/fixtures/mini_dart_gtfs/` fixture (3 routes, 8 stops)
that exercises every behavior asserted above.

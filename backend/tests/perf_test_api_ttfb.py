"""TTFB / API latency profile harness (T13.88).

This file is a *measurement* harness, not a pass/fail unit-test suite.
Pytest's default collection pattern (``test_*.py``) does not match
``perf_test_api_ttfb.py``, so it is invisible to ordinary test runs.
A second guard — the module-level ``RUN_PERF_TESTS`` env-var check —
skips the file when somebody invokes it explicitly without opting in.

Run with::

    cd backend
    RUN_PERF_TESTS=1 .venv/bin/python -m pytest \\
        tests/perf_test_api_ttfb.py -v -s

The ``-s`` flag is REQUIRED so the per-endpoint table prints to stdout.

What this harness does
======================

1. Discovers session-owned routes via :mod:`tests._route_inventory`.
2. Adds a curated list of public read endpoints (health, root,
   /api/city, dashboard stats, jobs list, outcomes aggregate,
   intelligence barriers).
3. For each endpoint, builds a representative payload using a seeded
   session + matching token so the request reaches the handler body
   (not just the auth gate).
4. Warms the app, then runs N=20 timed requests per endpoint via
   ``httpx.Client`` against ``TestClient``.
5. Computes p50 / p95 / p99 / min / max / mean.
6. Prints a Markdown table to stdout AND writes
   ``docs/qc-reports/S13-T88-api-perf.md`` with the full results.

Caveats are documented in the generated report (see
:mod:`tests._perf_report`).
"""
from __future__ import annotations

import os
import sqlite3
import statistics
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

if not os.environ.get("RUN_PERF_TESTS"):
    pytest.skip(
        "perf-only — set RUN_PERF_TESTS=1 to run",
        allow_module_level=True,
    )

# Heavyweight imports deferred until after the skip so this file is
# free for the rest of the suite.
from fastapi.testclient import TestClient

from app.core.migrations import runner
from tests import _perf_report
from tests._cross_session_fixtures import REQUIRED_FIELD_PLACEHOLDERS
from tests._route_inventory import (
    RouteSpec,
    all_route_specs,
    discover_session_routes,
)


# ---------------------------------------------------------------- constants

_SESS_ID_TEMPLATE = "{:08x}-1111-4111-8111-{:012x}"
_TOK_TEMPLATE = "tok-perf-{:08x}-{:012x}"

_N_REQUESTS = 20
_WARMUP_REQUESTS = 3

_PUBLIC_READ_ENDPOINTS: tuple[tuple[str, str], ...] = (
    ("GET", "/"),
    ("GET", "/health"),
    ("GET", "/health/live"),
    ("GET", "/health/ready"),
    ("GET", "/api/city"),
    ("GET", "/api/jobs/"),
    ("GET", "/api/dashboard/stats"),
    ("GET", "/api/outcomes/aggregate"),
    ("GET", "/api/intelligence/barriers"),
)

_SKIP_ROUTES: dict[str, str] = {
    # LLM-backed: real Anthropic call would dominate timing.
    "POST /api/plan/{session_id}/generate":
        "LLM-backed (Anthropic); upstream-dominated",
    "POST /api/documents/resume":
        "LLM-backed (Anthropic); upstream-dominated",
    "POST /api/documents/cover-letter":
        "LLM-backed (Anthropic); upstream-dominated",
    "POST /api/barrier-intel/chat":
        "LLM-backed (Anthropic); upstream-dominated",
    # Path-id resources requiring seeded child rows.
    "GET /api/appointments/{appointment_id}":
        "Path-id requires seeded appointment row",
    "PATCH /api/appointments/{appointment_id}":
        "Path-id requires seeded appointment row",
    "DELETE /api/appointments/{appointment_id}":
        "Path-id requires seeded appointment row",
    "POST /api/appointments/{appointment_id}/attended":
        "Path-id requires seeded appointment row",
    "POST /api/appointments/{appointment_id}/missed":
        "Path-id requires seeded appointment row",
    "PATCH /api/job-applications/{application_id}":
        "Path-id requires seeded application row",
    "GET /api/documents/resume/{version_id}":
        "Path-id requires seeded resume version row",
    "GET /api/documents/resume/{version_id}/pdf":
        "Path-id requires seeded resume version row",
    "GET /api/documents/cover-letter/{version_id}":
        "Path-id requires seeded cover-letter version row",
    "GET /api/documents/cover-letter/{version_id}/pdf":
        "Path-id requires seeded cover-letter version row",
}


# ---------------------------------------------------------------- helpers


def _percentiles(samples_ms: list[float]) -> dict[str, float]:
    """Return p50/p95/p99/min/max/mean (in ms) for a list of samples.

    Uses the "nearest rank" method::

        index = ceil(p/100 * N) - 1   (clamped to [0, N-1])

    For N=20 this gives p50 -> index 9 (value 10/20), p95 -> index 18
    (value 19/20), p99 -> index 19 (value 20/20). p99 saturates to the
    max sample when N <= ~100; this is documented in the report's
    Caveats section.
    """
    if not samples_ms:
        return {
            "p50": 0.0, "p95": 0.0, "p99": 0.0,
            "min": 0.0, "max": 0.0, "mean": 0.0,
        }
    s = sorted(samples_ms)
    n = len(s)
    return {
        "p50": s[_nearest_rank_index(0.50, n)],
        "p95": s[_nearest_rank_index(0.95, n)],
        "p99": s[_nearest_rank_index(0.99, n)],
        "min": s[0],
        "max": s[-1],
        "mean": statistics.fmean(s),
    }


def _nearest_rank_index(percentile: float, n: int) -> int:
    """Nearest-rank index for ``percentile`` in a sorted list of length ``n``.

    Returns ``ceil(percentile * n) - 1`` clamped to ``[0, n-1]``.
    """
    import math

    idx = math.ceil(percentile * n) - 1
    return max(0, min(n - 1, idx))


def profile_endpoint(
    client: TestClient,
    method: str,
    url: str,
    *,
    payload: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    n: int = _N_REQUESTS,
    warmup: int = _WARMUP_REQUESTS,
) -> dict[str, Any]:
    """Run timed requests against a single endpoint and return metrics."""
    for _ in range(warmup):
        client.request(method, url, params=params, json=payload, headers=headers)
    samples_ms: list[float] = []
    last_status = 0
    for _ in range(n):
        t0 = time.perf_counter()
        resp = client.request(
            method, url, params=params, json=payload, headers=headers,
        )
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        samples_ms.append(elapsed_ms)
        last_status = resp.status_code
    pcts = _percentiles(samples_ms)
    return {
        "method": method,
        "path": url,
        "n": n,
        "status_code": last_status,
        "samples_ms": samples_ms,
        **pcts,
    }


def _make_session_id(seq: int) -> str:
    return _SESS_ID_TEMPLATE.format(seq, seq)


def _make_token(seq: int) -> str:
    return _TOK_TEMPLATE.format(seq, seq)


def _build_args_for_session_route(
    spec: RouteSpec, sess_id: str, token: str,
) -> dict[str, Any]:
    """Construct (url, params, body) for a session-owned route.

    A unique ``sess_id`` + matching ``token`` is provided per endpoint
    so a destructive endpoint (e.g. POST /api/compliance/delete) cannot
    invalidate the auth context of any other endpoint in the run.
    """
    url = spec.path.replace("{session_id}", sess_id)
    params: dict[str, Any] = {}
    body: dict[str, Any] | None = None

    if spec.session_id_loc == "query":
        params["session_id"] = sess_id
    elif spec.session_id_loc == "body":
        body = {"session_id": sess_id}

    if spec.token_loc == "query":
        params[spec.token_name] = token
    elif spec.token_loc == "body":
        body = body if body is not None else {}
        body[spec.token_name] = token

    if spec.body_required_fields:
        body = body if body is not None else {}
        for field_name in spec.body_required_fields:
            body.setdefault(
                field_name,
                REQUIRED_FIELD_PLACEHOLDERS.get(field_name, "x"),
            )
    return {"url": url, "params": params, "body": body}


def _classify_skip_reason(method: str, path: str) -> str:
    """One-line rationale for an unprofiled route."""
    key = f"{method} {path}"
    if key in _SKIP_ROUTES:
        return _SKIP_ROUTES[key]
    if path.startswith("/api/admin/"):
        return "Admin-key gated; different trust boundary"
    if path.startswith("/api/advisor/"):
        return "Advisor auth; different trust boundary"
    if path.startswith("/api/brightdata/"):
        return "External (BrightData); upstream-dominated"
    if path.startswith("/api/webhooks/"):
        return "Webhook; signature-verified, not user-facing"
    if path.startswith("/api/demo/"):
        return "Admin-only demo bootstrap"
    if "share_token" in path or "/manage" in path:
        return "Signed-token auth; requires single-use token mint"
    if "feedback/validate" in path or "feedback/visit" in path:
        return "Token-only auth (no session_id); covered by T13.63"
    if path.startswith("/api/engagement/unsubscribe"):
        return "Signed-token auth; not session-scoped"
    if path.startswith("/api/engagement/send-now"):
        return "Admin-key gated; not session-scoped"
    if path.startswith("/api/compliance/export/download"):
        return "Single-use signed download token; mint required"
    if path.startswith("/api/credit/assess"):
        return "Anonymous self-assessment; profiled separately if needed"
    if path.startswith("/api/assessment/"):
        return "Creates a new session; mutates global state — separate harness"
    if "/job-applications/community-funnel" in path:
        return "Token-only resolves city; profiled if added to harness"
    if path.startswith("/api/jobs/{"):
        return "Path-id requires seeded job row"
    if path.startswith("/api/barrier-intel/reindex"):
        return "Admin-key gated reindex; not session-scoped"
    return "Not classified — review and add to harness or skip list"


def _public_read_targets() -> list[dict[str, Any]]:
    """Curated public read endpoints (no auth required)."""
    return [
        {
            "method": method, "path": path,
            "url": path, "params": None, "body": None,
            "session_id": None, "token": None,
        }
        for method, path in _PUBLIC_READ_ENDPOINTS
    ]


def _session_route_targets(
    client: TestClient,
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    """Profile-target + skip-entry lists for session-owned routes."""
    targets: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []
    for seq, spec in enumerate(discover_session_routes(client.app), start=1):
        key = f"{spec.method} {spec.path}"
        if key in _SKIP_ROUTES:
            skipped.append({
                "method": spec.method, "path": spec.path,
                "reason": _SKIP_ROUTES[key],
            })
            continue
        sess_id = _make_session_id(seq)
        token = _make_token(seq)
        args = _build_args_for_session_route(spec, sess_id, token)
        targets.append({
            "method": spec.method, "path": spec.path,
            "url": args["url"],
            "params": args["params"] or None,
            "body": args["body"],
            "session_id": sess_id, "token": token,
        })
    return targets, skipped


def _enumerate_targets(
    client: TestClient,
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    """Return (profile_targets, skipped_entries).

    Each session-owned target carries a unique ``session_id`` + ``token``
    pair (sequence-numbered) so destructive endpoints cannot trash one
    another's auth context. The caller is responsible for seeding those
    pairs into the DB before profiling — see :func:`_seed_session_pairs`.
    """
    targets = _public_read_targets()
    session_targets, skipped = _session_route_targets(client)
    targets.extend(session_targets)

    profiled_keys = {
        f"{t['method']} {t['path']}" for t in targets
    } | {f"{s['method']} {s['path']}" for s in skipped}
    for method, path in all_route_specs(client.app):
        key = f"{method} {path}"
        if key in profiled_keys:
            continue
        skipped.append({
            "method": method, "path": path,
            "reason": _classify_skip_reason(method, path),
        })
    return targets, skipped


def _seed_session_pairs(
    db_path: str, targets: list[dict[str, Any]],
) -> None:
    """Insert a session+feedback_token row for every session-owned target.

    Uses ``INSERT OR IGNORE`` so re-running the harness against an
    existing DB is a no-op rather than a uniqueness violation. Sessions
    expire 30 days from now so the rows survive the entire run.
    """
    pairs = [
        (t["session_id"], t["token"])
        for t in targets if t.get("session_id")
    ]
    if not pairs:
        return
    now = datetime.now(timezone.utc)
    expires = (now + timedelta(days=30)).isoformat()
    conn = sqlite3.connect(db_path)
    try:
        for sess_id, token in pairs:
            conn.execute(
                "INSERT OR IGNORE INTO sessions (id, created_at, "
                "barriers, profile, expires_at) VALUES (?, ?, ?, ?, ?)",
                (sess_id, now.isoformat(), "[]", "{}", expires),
            )
            conn.execute(
                "INSERT OR IGNORE INTO feedback_tokens (token, "
                "session_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
                (token, sess_id, now.isoformat(), expires),
            )
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------- fixtures


@pytest.fixture(scope="module")
def perf_db(tmp_path_factory: pytest.TempPathFactory) -> str:
    """Migrated SQLite DB. Per-endpoint session+token pairs are seeded
    later, once the harness knows how many session-owned targets there
    are (see :func:`_seed_session_pairs`).
    """
    db_path = str(tmp_path_factory.mktemp("perf") / "perf.db")
    runner.apply_pending(db_path)
    return db_path


@pytest.fixture(scope="module")
def perf_client(perf_db: str):
    """TestClient wired to the perf DB. Module-scoped so app boots once."""
    from app.core import config as config_mod
    from app.core import database as db_mod
    from app.routes import _appointments_helpers as auth_helpers

    original_resolver = auth_helpers.resolve_db_path
    auth_helpers.resolve_db_path = lambda: perf_db  # type: ignore[assignment]

    os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{perf_db}"
    config_mod.get_settings.cache_clear()
    old_engine = db_mod._engine
    old_factory = db_mod._async_session_factory
    db_mod._engine = None
    db_mod._async_session_factory = None

    from app.main import app
    client = TestClient(app, raise_server_exceptions=False)
    try:
        yield client
    finally:
        auth_helpers.resolve_db_path = original_resolver  # type: ignore[assignment]
        db_mod._engine = old_engine
        db_mod._async_session_factory = old_factory
        config_mod.get_settings.cache_clear()


# ---------------------------------------------------------------- runner


_REPORT_PATH = (
    Path(__file__).resolve().parents[2]
    / "docs" / "qc-reports" / "S13-T88-api-perf.md"
)


def _machine_label() -> str:
    return f"{sys.platform} / Python {sys.version.split()[0]}"


def _print_table(results: list[dict[str, Any]]) -> None:
    print("\n=== TTFB Results (ms, in-process TestClient, N=20) ===")
    for line in _perf_report.table_header():
        print(line)
    for r in sorted(results, key=lambda x: -x["p95"]):
        print(_perf_report.format_row(r))


def _write_report(
    results: list[dict[str, Any]],
    skipped: list[dict[str, str]],
) -> None:
    _REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = _perf_report.build_report_lines(
        results, skipped,
        n=_N_REQUESTS, warmup=_WARMUP_REQUESTS,
        machine=_machine_label(),
        generated=datetime.now(timezone.utc).date().isoformat(),
    )
    _REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def perf_test_profile_all_endpoints(perf_client, perf_db) -> None:
    """The driver: profile every target, print the table, write the report."""
    targets, skipped = _enumerate_targets(perf_client)
    _seed_session_pairs(perf_db, targets)
    results: list[dict[str, Any]] = []
    for t in targets:
        result = profile_endpoint(
            perf_client, t["method"], t["url"],
            payload=t["body"], params=t["params"],
        )
        result["path"] = t["path"]  # report shows the template path
        results.append(result)
    _print_table(results)
    _write_report(results, skipped)
    print(f"\nReport written to: {_REPORT_PATH}")
    print(f"Profiled: {len(results)} endpoints; Skipped: {len(skipped)}")


# Pytest collection: alias the runner to a ``test_`` name so that, when
# invoked with the file path explicitly + RUN_PERF_TESTS=1, pytest does
# pick it up. The ``perf_test_`` filename keeps it invisible to default
# collection.
test_profile_all_endpoints = perf_test_profile_all_endpoints

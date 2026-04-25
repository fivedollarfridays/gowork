"""Markdown report builder for the T13.88 TTFB harness.

Pure functions — given a list of profile result dicts and a list of
skipped-endpoint dicts, returns the report as a list of lines. Kept
separate from the harness so the harness itself stays under the test
file size limit and so this module can be unit-tested without booting
the FastAPI app.

Public surface
--------------
* :data:`READ_BUDGET_MS`, :data:`WRITE_BUDGET_MS` — budget thresholds in ms.
* :func:`budget_ms(method)` — budget for a method.
* :func:`status_for(p95_ms, method)` — "PASS" / "FAIL".
* :func:`format_row(result)` — single Markdown table row.
* :func:`table_header()` — list of two header lines (header + sep).
* :func:`build_report_lines(results, skipped, n, warmup, machine, generated)`
  — the full report body.
"""
from __future__ import annotations

from typing import Any


READ_BUDGET_MS = 500
WRITE_BUDGET_MS = 2000


def budget_ms(method: str) -> int:
    """Return the p95 budget (ms) for a request method."""
    return READ_BUDGET_MS if method.upper() == "GET" else WRITE_BUDGET_MS


def status_for(p95_ms: float, method: str) -> str:
    """PASS if within budget, else FAIL."""
    return "PASS" if p95_ms <= budget_ms(method) else "FAIL"


def format_row(result: dict[str, Any]) -> str:
    """Single Markdown table row for one endpoint result."""
    method = result["method"]
    return (
        f"| {method:<6} | {result['path']:<55} | "
        f"{result['p50']:7.1f} | {result['p95']:7.1f} | "
        f"{result['p99']:7.1f} | {result['min']:7.1f} | "
        f"{result['max']:7.1f} | {budget_ms(method):>4}ms | "
        f"{status_for(result['p95'], method):<5} | "
        f"{result['status_code']:>3} |"
    )


def table_header() -> list[str]:
    """Markdown table header rows (header + separator)."""
    return [
        (
            "| Method | Path                                                    "
            "|     p50 |     p95 |     p99 |     min |     max | Budget | "
            "Stat  | HTTP |"
        ),
        (
            "|--------|---------------------------------------------------------"
            "|---------|---------|---------|---------|---------|--------|"
            "-------|------|"
        ),
    ]


def build_report_lines(
    results: list[dict[str, Any]],
    skipped: list[dict[str, str]],
    *,
    n: int,
    warmup: int,
    machine: str,
    generated: str,
) -> list[str]:
    """Return the full S13-T88 report as a list of lines."""
    failures = [
        r for r in results if status_for(r["p95"], r["method"]) == "FAIL"
    ]
    slowest = sorted(results, key=lambda r: -r["p95"])[:5]
    out: list[str] = []
    out.extend(_header(results, skipped, failures, machine, generated))
    out.extend(_methodology(n, warmup))
    out.extend(_results_table(results))
    out.extend(_findings(failures))
    out.extend(_top5(slowest))
    out.extend(_skipped(skipped))
    out.extend(_caveats(warmup))
    out.extend(_recommendations(failures, slowest))
    return out


def _header(
    results: list[dict[str, Any]],
    skipped: list[dict[str, str]],
    failures: list[dict[str, Any]],
    machine: str,
    generated: str,
) -> list[str]:
    return [
        "# T13.88 — API TTFB / Latency Profile",
        "",
        "**Sprint:** S13",
        f"**Generated:** {generated}",
        "**Harness:** `backend/tests/perf_test_api_ttfb.py`",
        f"**Machine:** {machine}",
        f"**Endpoints profiled:** {len(results)}",
        f"**Endpoints skipped:** {len(skipped)}",
        f"**Endpoints failing budget:** {len(failures)}",
        "",
    ]


def _methodology(n: int, warmup: int) -> list[str]:
    return [
        "## Methodology",
        "",
        "- **Tool:** `httpx`-based `fastapi.testclient.TestClient`,"
        " in-process — no network jitter.",
        f"- **N:** {n} measured requests per endpoint (after {warmup}"
        " warmup calls).",
        "- **Timer:** `time.perf_counter()` around each `client.request("
        "...)` call.",
        "- **Payload:** representative — for session-owned routes, a"
        " single seeded session+token; for body-required routes, the"
        " same `REQUIRED_FIELD_PLACEHOLDERS` table T13.63 uses.",
        "- **DB:** ephemeral SQLite (per-module tmp dir) with all"
        " m001-m003 migrations applied.",
        f"- **Budgets:** read (GET) p95 ≤ {READ_BUDGET_MS}ms, write"
        f" (non-GET) p95 ≤ {WRITE_BUDGET_MS}ms.",
        "- **Categories used:** read = GET; write ="
        " POST/PUT/PATCH/DELETE.",
        "",
        "Status codes are printed for context — the harness does NOT",
        "filter on status. A 4xx is a real handler exit (auth check,",
        "404, etc.) and its TTFB is still the time to first byte.",
        "",
    ]


def _results_table(results: list[dict[str, Any]]) -> list[str]:
    head = table_header()
    body = [
        format_row(r)
        for r in sorted(results, key=lambda r: (-r["p95"], r["path"]))
    ]
    return ["## Per-endpoint results", "", *head, *body, ""]


def _findings(failures: list[dict[str, Any]]) -> list[str]:
    if not failures:
        return [
            "## Findings",
            "",
            "No endpoint exceeds its in-process budget. Real-world",
            "(cross-region network) latency will add ~50-200ms per call;",
            "see Caveats.",
            "",
        ]
    out = ["## Findings — endpoints exceeding budget", ""]
    for r in failures:
        out.extend(_finding_block(r))
    return out


def _finding_block(r: dict[str, Any]) -> list[str]:
    return [
        f"### {r['method']} {r['path']}",
        "",
        f"- **p95:** {r['p95']:.1f}ms (budget"
        f" {budget_ms(r['method'])}ms)",
        f"- **p99:** {r['p99']:.1f}ms",
        f"- **mean:** {r['mean']:.1f}ms / **min:** {r['min']:.1f}ms /"
        f" **max:** {r['max']:.1f}ms",
        f"- **Hypothesis:** {hypothesis_for(r)}",
        "",
    ]


def hypothesis_for(r: dict[str, Any]) -> str:
    """Best-guess explanation for a slow endpoint based on path patterns."""
    p = r["path"]
    if "/plan/" in p and "generate" in p:
        return "LLM client cold-load + Anthropic round-trip"
    if "/documents/" in p and r["method"] == "POST":
        return "LLM client cold-load + Anthropic round-trip"
    if "/pdf" in p:
        return "weasyprint render time"
    if "/barrier-intel" in p or "/insights" in p:
        return "sentence-transformers warmup + embedding compute"
    if "/refresh" in p:
        return "Plan refresher recomputes pathway + history insert"
    if r["method"] != "GET" and r["max"] / max(r["mean"], 1.0) > 3.0:
        return "SQLite write contention outlier (max >> mean)"
    return "Investigate handler — DB query plan or sync I/O on async route"


def _top5(slowest: list[dict[str, Any]]) -> list[str]:
    out = ["## Top 5 slowest endpoints by p95", ""]
    out.append("| Rank | Method | Path | p95 (ms) | Budget | Status |")
    out.append("|------|--------|------|----------|--------|--------|")
    for i, r in enumerate(slowest, 1):
        out.append(
            f"| {i} | {r['method']} | `{r['path']}` | "
            f"{r['p95']:.1f} | {budget_ms(r['method'])}ms | "
            f"{status_for(r['p95'], r['method'])} |"
        )
    out.append("")
    return out


def _skipped(skipped: list[dict[str, str]]) -> list[str]:
    out = ["## Skipped endpoints", "", f"**Count:** {len(skipped)}", ""]
    out.append("| Method | Path | Reason |")
    out.append("|--------|------|--------|")
    for s in sorted(skipped, key=lambda x: (x["path"], x["method"])):
        out.append(
            f"| {s['method']} | `{s['path']}` | {s['reason']} |"
        )
    out.append("")
    return out


def _caveats(warmup: int) -> list[str]:
    return [
        "## Caveats",
        "",
        "- **In-process bias.** `TestClient` runs the FastAPI app"
        " in-process via ASGI; there is no socket, no kernel TCP stack,",
        "  no TLS handshake. Real HTTP from a remote client adds"
        " roughly 50-200ms per request (cross-region) plus TLS setup",
        "  on cold connections. Real-world budgets should subtract that"
        " overhead from the local measurements before declaring health.",
        "- **Cold-start.** The first request after process boot pays for",
        "  module imports, lazy LLM-client init, and (where wired)",
        "  sentence-transformers model load. The harness fires"
        f" {warmup} warmup calls per endpoint before measuring",
        "  to absorb that cost; the warmups are NOT in the percentiles.",
        "- **SQLite write contention.** Single-writer locking causes",
        "  occasional outliers under burst write load. With N=20, p99 is",
        "  the worst single sample — useful as a tail indicator but not",
        "  a tight bound. A larger N (200+) would be needed for stable p99.",
        "- **No real network.** If a route's real bottleneck is an",
        "  outbound call (Anthropic, SendGrid, BrightData, OpenAI), this",
        "  harness will UNDERSTATE its latency. Those routes are skipped",
        "  here and tracked separately.",
        "",
    ]


def _recommendations(
    failures: list[dict[str, Any]],
    slowest: list[dict[str, Any]],
) -> list[str]:
    out = ["## Recommendations", ""]
    if not failures:
        out.append(
            "All profiled endpoints are within budget on the in-process"
            " harness. Recommendations focus on the worst-tail slice:"
        )
        out.append("")
    rank = 1
    for r in failures:
        out.append(
            f"{rank}. **{r['method']} {r['path']}** — "
            f"p95 {r['p95']:.0f}ms exceeds {budget_ms(r['method'])}ms"
            f" budget. {hypothesis_for(r)}. Investigate handler + add"
            f" caching or move expensive work off the request path."
        )
        rank += 1
    if not failures:
        for r in slowest[:3]:
            out.append(
                f"{rank}. **{r['method']} {r['path']}** — "
                f"p95 {r['p95']:.0f}ms (budget"
                f" {budget_ms(r['method'])}ms). Within budget but at the"
                f" top of the list — keep an eye on it as feature scope"
                f" grows. {hypothesis_for(r)}."
            )
            rank += 1
    out.extend([
        "",
        "**Cross-cutting:**",
        "",
        "- Ensure async routes don't fall back to sync I/O (sqlite3"
        " inside an async handler will block the event loop).",
        "- Add request-scoped query counters in dev to spot N+1 patterns"
        " before they hit the perf budget.",
        "- For LLM-backed routes, consider a 'preview cached' fast path"
        " that returns the last good output while a background job"
        " refreshes — keeps the user-facing TTFB low.",
        "- Re-run this harness after any router refactor; commit the new"
        " report alongside the change.",
        "",
    ])
    return out


__all__ = [
    "READ_BUDGET_MS",
    "WRITE_BUDGET_MS",
    "budget_ms",
    "status_for",
    "format_row",
    "table_header",
    "build_report_lines",
    "hypothesis_for",
]

"""Unit tests for the T13.88 TTFB report-builder helpers.

These tests exercise :mod:`tests._perf_report` (pure functions) and the
``_percentiles`` helper inside :mod:`tests.perf_test_api_ttfb` without
booting the FastAPI app — they use a stub TestClient where needed.

We deliberately do NOT collect ``perf_test_api_ttfb.py`` itself
(default pytest pattern excludes it, and the harness is gated on
``RUN_PERF_TESTS``); instead, these tests verify the math + Markdown
formatting that the harness depends on so a regression here is caught
in the regular test suite.
"""
from __future__ import annotations

import importlib

import pytest

from tests import _perf_report


# ---------------------------------------------------------------- budget


def test_budget_get_is_500ms() -> None:
    assert _perf_report.budget_ms("GET") == 500


def test_budget_post_is_2000ms() -> None:
    assert _perf_report.budget_ms("POST") == 2000


def test_budget_patch_is_2000ms() -> None:
    assert _perf_report.budget_ms("PATCH") == 2000


def test_budget_lowercase_get_still_classified_as_read() -> None:
    assert _perf_report.budget_ms("get") == 500


# ---------------------------------------------------------------- status


def test_status_pass_when_p95_under_budget() -> None:
    assert _perf_report.status_for(100.0, "GET") == "PASS"


def test_status_fail_when_p95_over_budget() -> None:
    assert _perf_report.status_for(600.0, "GET") == "FAIL"


def test_status_exact_boundary_is_pass() -> None:
    assert _perf_report.status_for(500.0, "GET") == "PASS"
    assert _perf_report.status_for(2000.0, "POST") == "PASS"


# ---------------------------------------------------------------- format_row


def _sample_result(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "method": "GET", "path": "/api/x",
        "p50": 10.0, "p95": 50.0, "p99": 80.0,
        "min": 5.0, "max": 100.0, "mean": 25.0,
        "status_code": 200, "n": 20, "samples_ms": [],
    }
    base.update(overrides)
    return base


def test_format_row_includes_method_and_path() -> None:
    row = _perf_report.format_row(_sample_result())
    assert "GET" in row
    assert "/api/x" in row


def test_format_row_marks_pass_when_under_budget() -> None:
    row = _perf_report.format_row(_sample_result(p95=10.0))
    assert "PASS" in row
    assert "FAIL" not in row


def test_format_row_marks_fail_when_over_budget() -> None:
    row = _perf_report.format_row(_sample_result(p95=900.0))
    assert "FAIL" in row


def test_format_row_includes_http_status() -> None:
    row = _perf_report.format_row(_sample_result(status_code=403))
    assert "403" in row


# ---------------------------------------------------------------- header


def test_table_header_returns_two_rows() -> None:
    head = _perf_report.table_header()
    assert len(head) == 2
    assert head[0].startswith("|") and head[0].endswith("|")
    assert "p95" in head[0]
    # second row is the separator
    assert set(head[1]) <= set("|-")


# ---------------------------------------------------------------- hypothesis


def test_hypothesis_for_plan_generate_mentions_llm() -> None:
    r = _sample_result(method="POST", path="/api/plan/{session_id}/generate")
    h = _perf_report.hypothesis_for(r)
    assert "LLM" in h


def test_hypothesis_for_pdf_route_mentions_weasyprint() -> None:
    r = _sample_result(method="GET", path="/api/documents/resume/1/pdf")
    h = _perf_report.hypothesis_for(r)
    assert "weasyprint" in h.lower()


def test_hypothesis_for_insights_mentions_embeddings() -> None:
    r = _sample_result(method="GET", path="/api/insights/{session_id}")
    h = _perf_report.hypothesis_for(r)
    assert "embedding" in h.lower() or "sentence-transformers" in h.lower()


def test_hypothesis_for_outlier_write_mentions_contention() -> None:
    r = _sample_result(method="POST", path="/api/x", mean=10.0, max=100.0)
    h = _perf_report.hypothesis_for(r)
    assert "contention" in h.lower() or "outlier" in h.lower()


def test_hypothesis_for_unmatched_falls_back_to_generic() -> None:
    r = _sample_result(method="GET", path="/api/something/new")
    h = _perf_report.hypothesis_for(r)
    assert "Investigate" in h or "DB" in h


# ---------------------------------------------------------------- report


def test_build_report_includes_required_sections() -> None:
    results = [_sample_result()]
    report = "\n".join(_perf_report.build_report_lines(
        results, [], n=20, warmup=3,
        machine="darwin", generated="2026-04-24",
    ))
    for section in (
        "T13.88",
        "## Methodology",
        "## Per-endpoint results",
        "## Findings",
        "## Top 5 slowest endpoints by p95",
        "## Skipped endpoints",
        "## Caveats",
        "## Recommendations",
    ):
        assert section in report, f"missing section: {section}"


def test_build_report_findings_clean_when_no_failures() -> None:
    results = [_sample_result(p95=50.0)]
    report = "\n".join(_perf_report.build_report_lines(
        results, [], n=20, warmup=3, machine="m", generated="d",
    ))
    assert "No endpoint exceeds its in-process budget" in report


def test_build_report_findings_lists_failures() -> None:
    results = [_sample_result(method="GET", path="/slow", p95=600.0)]
    report = "\n".join(_perf_report.build_report_lines(
        results, [], n=20, warmup=3, machine="m", generated="d",
    ))
    assert "exceeds 500ms budget" in report or "endpoints exceeding budget" in report
    assert "/slow" in report


def test_build_report_skipped_table_lists_each_skip() -> None:
    skipped = [
        {"method": "POST", "path": "/skip-me", "reason": "external"},
    ]
    report = "\n".join(_perf_report.build_report_lines(
        [_sample_result()], skipped,
        n=20, warmup=3, machine="m", generated="d",
    ))
    assert "/skip-me" in report
    assert "external" in report


def test_build_report_caveats_mention_cold_start_and_network() -> None:
    report = "\n".join(_perf_report.build_report_lines(
        [_sample_result()], [],
        n=20, warmup=3, machine="m", generated="d",
    ))
    assert "Cold-start" in report
    assert "In-process" in report
    assert "SQLite" in report


def test_build_report_machine_label_appears_in_header() -> None:
    report = "\n".join(_perf_report.build_report_lines(
        [_sample_result()], [],
        n=20, warmup=3, machine="apple-m4-darwin", generated="2026-04-24",
    ))
    assert "apple-m4-darwin" in report
    assert "2026-04-24" in report


# ---------------------------------------------------------------- percentiles


@pytest.fixture
def percentiles_fn() -> object:
    """Load the harness's _percentiles helper without triggering the skip.

    The harness file uses ``pytest.skip(allow_module_level=True)`` when
    ``RUN_PERF_TESTS`` is not set, which prevents a normal import. We
    set the env var FOR THIS IMPORT ONLY so the function is reachable;
    the import does NOT fire any FastAPI boot or run any test bodies.
    """
    import os as _os

    prev = _os.environ.get("RUN_PERF_TESTS")
    _os.environ["RUN_PERF_TESTS"] = "1"
    try:
        mod = importlib.import_module("tests.perf_test_api_ttfb")
    finally:
        if prev is None:
            _os.environ.pop("RUN_PERF_TESTS", None)
        else:
            _os.environ["RUN_PERF_TESTS"] = prev
    return mod._percentiles


def test_percentiles_empty_returns_zeros(percentiles_fn) -> None:
    result = percentiles_fn([])
    for k in ("p50", "p95", "p99", "min", "max", "mean"):
        assert result[k] == 0.0


def test_percentiles_single_sample(percentiles_fn) -> None:
    result = percentiles_fn([42.0])
    assert result["p50"] == 42.0
    assert result["p95"] == 42.0
    assert result["p99"] == 42.0
    assert result["min"] == 42.0
    assert result["max"] == 42.0
    assert result["mean"] == 42.0


def test_percentiles_sorted_input(percentiles_fn) -> None:
    samples = list(range(1, 21))  # 1..20, mean 10.5
    result = percentiles_fn([float(x) for x in samples])
    assert result["min"] == 1.0
    assert result["max"] == 20.0
    assert result["p50"] == 10.0  # index int(0.5 * 19) = 9 -> sample 10
    # p95 uses ceil-style index: int(0.95 * 19 + 0.999) = int(18.049) = 18 -> sample 19
    assert result["p95"] == 19.0
    # p99: int(0.99 * 19 + 0.999) = int(19.809) = 19 -> sample 20
    assert result["p99"] == 20.0


def test_percentiles_unsorted_input_still_correct(percentiles_fn) -> None:
    samples = [20.0, 1.0, 10.0, 5.0, 15.0]
    result = percentiles_fn(samples)
    assert result["min"] == 1.0
    assert result["max"] == 20.0
    assert result["p50"] == 10.0

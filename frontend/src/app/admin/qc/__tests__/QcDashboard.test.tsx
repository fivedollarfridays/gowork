import { describe, it, expect } from "vitest";
import { render, screen, within } from "@testing-library/react";
import { QcDashboard } from "../QcDashboard";
import type { SuiteSummary } from "@/lib/qc/types";

function summary(overrides: Partial<SuiteSummary>): SuiteSummary {
  return {
    suite_id: "x",
    suite_name: "X",
    latest_verdict: "passed",
    latest_run_at: "2026-04-25T10:00:00Z",
    is_flaky: false,
    pass_rate_7d: 1,
    run_count_7d: 1,
    total_runs: 1,
    ...overrides,
  };
}

describe("QcDashboard", () => {
  it("renders the empty state when there are no summaries", () => {
    render(<QcDashboard summaries={[]} generatedAt="2026-04-25T12:00:00Z" />);
    expect(screen.getByText(/No QC runs yet/i)).toBeInTheDocument();
    expect(screen.getByText(/run-qc/i)).toBeInTheDocument();
  });

  it("renders one row per suite with the right indicator", () => {
    const passing = summary({
      suite_id: "worker-onboarding",
      suite_name: "Worker Onboarding",
      latest_verdict: "passed",
      is_flaky: false,
    });
    const failing = summary({
      suite_id: "advisor-send-note",
      suite_name: "Advisor Send Note",
      latest_verdict: "failed",
      is_flaky: false,
      pass_rate_7d: 0,
    });
    const flaky = summary({
      suite_id: "admin-flag-toggle",
      suite_name: "Admin Flag Toggle",
      latest_verdict: "passed",
      is_flaky: true,
      pass_rate_7d: 0.5,
    });

    render(
      <QcDashboard
        summaries={[passing, failing, flaky]}
        generatedAt="2026-04-25T12:00:00Z"
      />,
    );

    const passingRow = screen.getByTestId("suite-row-worker-onboarding");
    expect(within(passingRow).getByText(/pass/i)).toBeInTheDocument();

    const failingRow = screen.getByTestId("suite-row-advisor-send-note");
    expect(within(failingRow).getByText(/fail/i)).toBeInTheDocument();

    const flakyRow = screen.getByTestId("suite-row-admin-flag-toggle");
    expect(within(flakyRow).getByText(/flake/i)).toBeInTheDocument();
  });

  it("sorts failing first, then flaky, then by latest_run_at desc", () => {
    const summaries: SuiteSummary[] = [
      summary({
        suite_id: "old-pass",
        latest_verdict: "passed",
        latest_run_at: "2026-04-20T10:00:00Z",
      }),
      summary({
        suite_id: "new-pass",
        latest_verdict: "passed",
        latest_run_at: "2026-04-25T10:00:00Z",
      }),
      summary({
        suite_id: "the-failing",
        latest_verdict: "failed",
        latest_run_at: "2026-04-23T10:00:00Z",
      }),
      summary({
        suite_id: "the-flaky",
        latest_verdict: "passed",
        is_flaky: true,
        latest_run_at: "2026-04-22T10:00:00Z",
      }),
    ];

    render(
      <QcDashboard summaries={summaries} generatedAt="2026-04-25T12:00:00Z" />,
    );

    const rows = screen.getAllByTestId(/^suite-row-/);
    const ids = rows.map((r) => r.getAttribute("data-testid"));
    expect(ids).toEqual([
      "suite-row-the-failing",
      "suite-row-the-flaky",
      "suite-row-new-pass",
      "suite-row-old-pass",
    ]);
  });

  it("shows summary cards for total suites + total runs + overall pass rate", () => {
    const summaries: SuiteSummary[] = [
      summary({ suite_id: "a", run_count_7d: 3, pass_rate_7d: 1 }),
      summary({ suite_id: "b", run_count_7d: 2, pass_rate_7d: 0 }),
    ];
    render(
      <QcDashboard summaries={summaries} generatedAt="2026-04-25T12:00:00Z" />,
    );
    expect(screen.getByTestId("stat-total-suites")).toHaveTextContent("2");
    expect(screen.getByTestId("stat-runs-7d")).toHaveTextContent("5");
    // Overall pass rate is computed from per-suite rates weighted by runs:
    // (3*1 + 2*0) / 5 = 0.6
    expect(screen.getByTestId("stat-pass-rate-7d")).toHaveTextContent("60%");
  });
});

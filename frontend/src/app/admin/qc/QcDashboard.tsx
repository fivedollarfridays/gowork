/**
 * QC Dashboard presentational component (T13.8).
 *
 * Pure / props-driven so it's easy to unit-test. The server component
 * `page.tsx` is responsible for reading `.paircoder/qc/runs/`, parsing
 * JSON, and rolling up suite summaries; this view just renders them.
 */

import {
  dashboardStats,
  sortSummaries,
  verdictBadge,
  verdictLabel,
} from "@/lib/qc/dashboard";
import type { SuiteSummary } from "@/lib/qc/types";

interface QcDashboardProps {
  summaries: SuiteSummary[];
  generatedAt: string;
}

function formatPct(rate: number | null): string {
  if (rate == null) return "—";
  return `${Math.round(rate * 100)}%`;
}

function formatRelative(iso: string | null): string {
  if (!iso) return "never";
  return new Date(iso).toISOString().replace("T", " ").slice(0, 16) + " UTC";
}

function StatCards({ summaries }: { summaries: SuiteSummary[] }) {
  const stats = dashboardStats(summaries);
  return (
    <div className="grid gap-4 sm:grid-cols-3">
      <div className="rounded-lg border p-4">
        <div className="text-sm text-muted-foreground">Total suites</div>
        <div data-testid="stat-total-suites" className="text-3xl font-bold">
          {stats.total_suites}
        </div>
      </div>
      <div className="rounded-lg border p-4">
        <div className="text-sm text-muted-foreground">Runs (last 7d)</div>
        <div data-testid="stat-runs-7d" className="text-3xl font-bold">
          {stats.total_runs_7d}
        </div>
      </div>
      <div className="rounded-lg border p-4">
        <div className="text-sm text-muted-foreground">Pass rate (7d)</div>
        <div data-testid="stat-pass-rate-7d" className="text-3xl font-bold">
          {formatPct(stats.overall_pass_rate_7d)}
        </div>
      </div>
    </div>
  );
}

function SuiteRow({ summary }: { summary: SuiteSummary }) {
  const label = verdictLabel(summary.latest_verdict, summary.is_flaky);
  const badge = verdictBadge(summary.latest_verdict, summary.is_flaky);
  return (
    <tr
      data-testid={`suite-row-${summary.suite_id}`}
      className="border-b last:border-b-0"
    >
      <td className="py-2 px-3 font-mono text-sm">{summary.suite_id}</td>
      <td className="py-2 px-3">
        <span className="inline-flex items-center gap-1">
          <span aria-hidden="true">{badge}</span>
          <span>{label}</span>
        </span>
      </td>
      <td className="py-2 px-3 text-sm text-muted-foreground">
        {formatRelative(summary.latest_run_at)}
      </td>
      <td className="py-2 px-3 text-sm">{formatPct(summary.pass_rate_7d)}</td>
      <td className="py-2 px-3 text-sm text-muted-foreground">
        {summary.run_count_7d}
      </td>
    </tr>
  );
}

function EmptyState() {
  return (
    <div className="rounded-lg border border-dashed p-8 text-center">
      <p className="text-sm text-muted-foreground">
        No QC runs yet. Run a suite via{" "}
        <code className="rounded bg-muted px-1">/run-qc &lt;suite-id&gt;</code>{" "}
        to populate this dashboard.
      </p>
    </div>
  );
}

export function QcDashboard({ summaries, generatedAt }: QcDashboardProps) {
  const sorted = sortSummaries(summaries);
  return (
    <main className="min-h-screen px-4 py-8 sm:px-8">
      <div className="mx-auto max-w-5xl space-y-6">
        <header className="space-y-1">
          <h1 className="text-3xl font-bold">QC Dashboard</h1>
          <p className="text-sm text-muted-foreground">
            Generated {formatRelative(generatedAt)}
          </p>
        </header>

        <StatCards summaries={summaries} />

        {sorted.length === 0 ? (
          <EmptyState />
        ) : (
          <div className="rounded-lg border overflow-x-auto">
            <table className="w-full text-left">
              <thead className="bg-muted/50 text-xs uppercase tracking-wide text-muted-foreground">
                <tr>
                  <th className="py-2 px-3">Suite</th>
                  <th className="py-2 px-3">Latest</th>
                  <th className="py-2 px-3">Last run</th>
                  <th className="py-2 px-3">7d pass rate</th>
                  <th className="py-2 px-3">7d runs</th>
                </tr>
              </thead>
              <tbody>
                {sorted.map((s) => (
                  <SuiteRow key={s.suite_id} summary={s} />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </main>
  );
}

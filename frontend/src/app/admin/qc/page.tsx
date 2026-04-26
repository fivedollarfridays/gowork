/**
 * QC Dashboard server component (T13.8).
 *
 * Reads `.paircoder/qc/runs/` at request time (no build-time caching)
 * so re-running a suite shows up on the next refresh without a redeploy.
 *
 * Auth gating:
 *   - dev / test: open (this is the hackathon-grader view)
 *   - prod: require X-Admin-Key header to match `QC_DASHBOARD_ADMIN_KEY`,
 *     fail-closed if the env var is unset (returns 404 via notFound()).
 *
 * Runs directory resolution:
 *   - `QC_RUNS_DIR` env var if set (use this in prod deploys to point
 *     at a baked-in or volume-mounted runs dir)
 *   - else `<repo-root>/.paircoder/qc/runs/` for local dev. We resolve
 *     this from `process.cwd()`, which Next.js always sets to the
 *     project root when running `next dev` / `next start`.
 */

import { headers } from "next/headers";
import { notFound } from "next/navigation";
import path from "node:path";

import { groupBySuite } from "@/lib/qc/loader";
import { loadRunsFromDir } from "@/lib/qc/runs_dir";
import { summarizeSuite } from "@/lib/qc/trend";
import type { SuiteSummary } from "@/lib/qc/types";

import { QcDashboard } from "./QcDashboard";
import { isAccessAllowed } from "./access";

// Force this page to be rendered on every request — never statically
// optimized. The runs directory changes whenever a suite is re-run.
export const dynamic = "force-dynamic";
export const revalidate = 0;

function resolveRunsDir(): string {
  const fromEnv = process.env.QC_RUNS_DIR;
  if (fromEnv && fromEnv.trim().length > 0) return fromEnv;
  // `next dev` / `next start` run with cwd = repo root (frontend/), so
  // the .paircoder dir is one level up.
  return path.resolve(process.cwd(), "..", ".paircoder", "qc", "runs");
}

async function checkAccess(): Promise<void> {
  const hdrs = await headers();
  const allowed = isAccessAllowed({
    nodeEnv: process.env.NODE_ENV,
    headerKey: hdrs.get("x-admin-key"),
    adminKey: process.env.QC_DASHBOARD_ADMIN_KEY,
  });
  if (!allowed) notFound();
}

function buildSummaries(runsDir: string, now: Date): SuiteSummary[] {
  const runs = loadRunsFromDir(runsDir);
  const grouped = groupBySuite(runs);
  const summaries: SuiteSummary[] = [];
  for (const [suiteId, suiteRuns] of grouped.entries()) {
    summaries.push(summarizeSuite(suiteId, suiteRuns, now));
  }
  return summaries;
}

export default async function QcDashboardPage() {
  await checkAccess();
  const now = new Date();
  const runsDir = resolveRunsDir();
  const summaries = buildSummaries(runsDir, now);
  return <QcDashboard summaries={summaries} generatedAt={now.toISOString()} />;
}

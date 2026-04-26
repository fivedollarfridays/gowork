/**
 * Types for QC dashboard (T13.8).
 *
 * Mirrors the JSON output divona writes to `.paircoder/qc/runs/`
 * (see `.claude/agents/divona.md` Structured Output Format).
 *
 * Filename convention: `<suite-id>-<ISO8601-timestamp>.json`
 */

export type ScenarioVerdict = "passed" | "failed" | "skipped" | "error";

export type SuiteVerdict = ScenarioVerdict | "unknown";

export interface QcStep {
  step_description: string;
  verdict: ScenarioVerdict;
  observation?: string;
  duration_s?: number;
}

export interface QcScenario {
  name: string;
  verdict: ScenarioVerdict;
  failure_reason?: string;
  steps?: QcStep[];
}

/**
 * One QC run as written to `.paircoder/qc/runs/<suite-id>-<ts>.json`.
 *
 * `suite_id` and `timestamp` are populated from the filename when the
 * raw divona JSON omits them (the agent's documented schema doesn't
 * include either field — they live in the filename).
 */
export interface QcRun {
  suite_id: string;
  suite_name: string;
  environment: string;
  timestamp: string; // ISO 8601
  scenarios: QcScenario[];
}

export interface SuiteSummary {
  suite_id: string;
  suite_name: string;
  latest_verdict: SuiteVerdict;
  latest_run_at: string | null;
  is_flaky: boolean;
  pass_rate_7d: number | null; // null when no runs in window
  run_count_7d: number;
  total_runs: number;
}

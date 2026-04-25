/**
 * Run-file loader for the QC dashboard (T13.8).
 *
 * Parses `<suite-id>-<ISO8601-timestamp>.json` files written by divona
 * (see `.claude/agents/divona.md` Structured Output Format). The agent
 * doesn't include `suite_id` or `timestamp` fields in its JSON — both
 * live in the filename, so we hydrate them here.
 *
 * The dashboard reads these from the filesystem at request time
 * (server component); see `frontend/src/app/admin/qc/page.tsx`.
 */

import type { QcRun } from "./types";

/**
 * Filename pattern: `<suite-id>-YYYY-MM-DDTHH-MM-SS.json`.
 *
 * We use `-` separators in the time portion because `:` is reserved on
 * some filesystems. The trailing `-`-joined date/time tokens are the
 * timestamp; everything before them is the suite id. Numbered capture
 * groups (not named) for ES2017 target compat.
 */
const FILENAME_RE =
  /^(.+)-(\d{4}-\d{2}-\d{2})T(\d{2})-(\d{2})-(\d{2})\.json$/;

export interface ParsedFilename {
  suite_id: string;
  timestamp: string;
}

export function suiteIdFromFilename(filename: string): ParsedFilename | null {
  const match = FILENAME_RE.exec(filename);
  if (!match) return null;
  const [, suite, date, h, m, s] = match;
  return {
    suite_id: suite,
    timestamp: `${date}T${h}:${m}:${s}Z`,
  };
}

/**
 * Parse one run-file's JSON into a QcRun. Returns null if the JSON is
 * malformed or the filename doesn't match the expected pattern — the
 * dashboard treats unparseable files as missing rather than crashing.
 */
export function parseRunFile(filename: string, contents: string): QcRun | null {
  const parsed = suiteIdFromFilename(filename);
  if (!parsed) return null;
  let raw: Record<string, unknown>;
  try {
    raw = JSON.parse(contents) as Record<string, unknown>;
  } catch {
    return null;
  }
  const scenarios = Array.isArray(raw.scenarios) ? raw.scenarios : [];
  return {
    suite_id: parsed.suite_id,
    suite_name:
      typeof raw.suite_name === "string" ? raw.suite_name : parsed.suite_id,
    environment:
      typeof raw.environment === "string" ? raw.environment : "unknown",
    timestamp: parsed.timestamp,
    scenarios: scenarios as QcRun["scenarios"],
  };
}

/** Group runs by `suite_id` for per-suite roll-up. */
export function groupBySuite(runs: QcRun[]): Map<string, QcRun[]> {
  const map = new Map<string, QcRun[]>();
  for (const run of runs) {
    const list = map.get(run.suite_id);
    if (list) {
      list.push(run);
    } else {
      map.set(run.suite_id, [run]);
    }
  }
  return map;
}

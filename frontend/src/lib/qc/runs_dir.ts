/**
 * Filesystem reader for `.paircoder/qc/runs/` (T13.8).
 *
 * Used by the server-rendered QC dashboard at `/admin/qc`. Only loads
 * the immediate directory — subdirectories are ignored to keep the
 * read deterministic and fast on every request.
 *
 * In production, set `QC_RUNS_DIR` to the path of the runs directory
 * inside the deployed image, or the page will report "no runs".
 */

import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";

import { parseRunFile } from "./loader";
import type { QcRun } from "./types";

export function loadRunsFromDir(dir: string): QcRun[] {
  if (!existsSync(dir)) return [];
  let entries: string[];
  try {
    entries = readdirSync(dir);
  } catch {
    return [];
  }
  const runs: QcRun[] = [];
  for (const name of entries) {
    if (!name.endsWith(".json")) continue;
    const fullPath = join(dir, name);
    try {
      const stats = statSync(fullPath);
      if (!stats.isFile()) continue;
    } catch {
      continue;
    }
    let contents: string;
    try {
      contents = readFileSync(fullPath, "utf-8");
    } catch {
      continue;
    }
    const run = parseRunFile(name, contents);
    if (run) runs.push(run);
  }
  return runs;
}

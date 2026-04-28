#!/usr/bin/env node
/**
 * W4 Driver C Spotlight #3 — lighthouse-budget-diff CLI shim.
 *
 * Reads two Lighthouse JSON outputs (typically `prev/manifest.json` and
 * `current/manifest.json` from `lhci collect --upload.target=filesystem`)
 * and prints the per-category score deltas. Exits 1 on any regression
 * larger than REGRESSION_THRESHOLD_PTS (5).
 *
 * Heavy lifting lives in scripts/lib/lighthouse-budget-diff.mjs (testable
 * with vitest). This shim handles fs reading + process.exit only.
 *
 * Usage:
 *   node scripts/lighthouse-budget-diff.mjs prev.json current.json
 *   # exits 1 if any category dropped more than 5 points
 *
 * CI integration (future):
 *   - PR check downloads previous main lhci result, compares to current
 *     branch's run, fails the build on regression.
 *
 * @module
 */
import { readFileSync } from "node:fs";
import {
  diffSummaries,
  extractCategoryScores,
  formatDiffReport,
} from "./lib/lighthouse-budget-diff.mjs";

function loadRun(path) {
  const text = readFileSync(path, "utf-8");
  const parsed = JSON.parse(text);
  // Accept both single-run JSON and lhci manifest.json (an array of rows).
  if (Array.isArray(parsed)) {
    // Manifest array — pick the row matching the homepage `/` URL when
    // present, else first entry. Manifest rows carry `summary`.
    const homepage = parsed.find((r) => typeof r.url === "string" && r.url.endsWith("/"));
    return homepage ?? parsed[0];
  }
  return parsed;
}

const [, , prevPath, currPath] = process.argv;
if (!prevPath || !currPath) {
  console.error("Usage: lighthouse-budget-diff <prev.json> <current.json>");
  process.exit(2);
}

const prev = extractCategoryScores(loadRun(prevPath));
const curr = extractCategoryScores(loadRun(currPath));
const summary = diffSummaries(prev, curr);
console.log(formatDiffReport(summary));

if (summary.anyRegression) process.exit(1);

#!/usr/bin/env node
/**
 * T1.13 — WCAG AAA contrast CLI shim.
 *
 * Reads frontend/src/app/styles/tokens/colors.css, parses hex tokens, and
 * runs the AAA contrast report. Exits 1 on any FAIL.
 *
 * The heavy lifting lives in scripts/lib/contrast.ts (testable with vitest).
 * This shim exists for npm script + CI invocation.
 *
 * Usage: npm run contrast
 */

import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { runContrastReport } from "./lib/contrast.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const COLORS_CSS = resolve(HERE, "..", "src", "app", "styles", "tokens", "colors.css");

const css = readFileSync(COLORS_CSS, "utf-8");
const report = runContrastReport(css);

const headline = report.ok ? "WCAG AAA contrast: PASS" : "WCAG AAA contrast: FAIL";
console.log(`\n${headline}\n${"=".repeat(headline.length)}`);
for (const r of report.results) {
  console.log(r.line);
}
if (!report.ok) {
  console.log(`\n${report.failures.length} pair(s) below threshold.`);
  process.exit(1);
}
console.log(`\nAll ${report.results.length} pair(s) above threshold.`);

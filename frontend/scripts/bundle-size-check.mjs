#!/usr/bin/env node
// Bundle size CI gate (T13.87).
//
// Runs `next build` (or reads stdout from a prior run via --stdin), parses
// the per-route First Load JS table, and fails if any route exceeds its
// baseline by more than +10%.
//
// Usage:
//   node scripts/bundle-size-check.mjs           # spawns `npm run build`
//   node scripts/bundle-size-check.mjs --stdin   # reads build output from stdin
//   node scripts/bundle-size-check.mjs --threshold 15  # custom pct threshold
//
// Baseline lives in frontend/baseline-bundle-sizes.json. To update after an
// intentional regression, copy fresh values from `npm run build` output and
// commit the updated baseline file.

import { readFileSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import {
  parseBuildOutput,
  compareToBaseline,
  formatReport,
} from "./lib/bundle-size-parser.mjs";

const __dirname = dirname(fileURLToPath(import.meta.url));
const FRONTEND_ROOT = resolve(__dirname, "..");
const BASELINE_PATH = resolve(FRONTEND_ROOT, "baseline-bundle-sizes.json");

function parseArgs(argv) {
  const args = { stdin: false, threshold: undefined };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--stdin") args.stdin = true;
    else if (a === "--threshold") args.threshold = Number(argv[++i]);
  }
  return args;
}

async function readStdin() {
  const chunks = [];
  for await (const chunk of process.stdin) chunks.push(chunk);
  return Buffer.concat(chunks).toString("utf8");
}

function runBuild() {
  const result = spawnSync("npm", ["run", "build"], {
    cwd: FRONTEND_ROOT,
    encoding: "utf8",
    env: { ...process.env, NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000" },
  });
  if (result.status !== 0) {
    console.error("npm run build failed:");
    console.error(result.stderr || result.stdout);
    process.exit(2);
  }
  return result.stdout;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const baselineRaw = readFileSync(BASELINE_PATH, "utf8");
  const baselineJson = JSON.parse(baselineRaw);
  const baseline = baselineJson.routes || {};
  const threshold =
    args.threshold !== undefined
      ? args.threshold
      : Number(baselineJson._meta?.threshold_pct ?? 10);

  const stdout = args.stdin ? await readStdin() : runBuild();
  const current = parseBuildOutput(stdout);

  if (Object.keys(current).length === 0) {
    console.error(
      "No route table found in build output. Did the build emit the 'Route (app)' table?",
    );
    process.exit(2);
  }

  const result = compareToBaseline(current, baseline, threshold);
  console.log(formatReport(current, baseline, result, threshold));

  process.exit(result.ok ? 0 : 1);
}

main().catch((err) => {
  console.error(err);
  process.exit(2);
});

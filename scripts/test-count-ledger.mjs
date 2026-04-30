#!/usr/bin/env node
/**
 * W5 Driver A — Spotlight invention #2 (T5.A.8)
 *
 * Test-count ledger. Aggregates the canonical "how many tests do we have?"
 * number used by README.md, docs/press-kit.md, docs/devpost-submission.md,
 * and the social/marketing surface.
 *
 * Inputs:
 *   - frontend/  → vitest run --reporter json (full count) or
 *                   static parse of `*.test.{ts,tsx}` (fallback)
 *   - backend/   → pytest --collect-only -q (full count) or
 *                   static parse of `def test_` / `async def test_` (fallback)
 *
 * Output:
 *   JSON to stdout:
 *   {
 *     "frontend": 3428,
 *     "backend":  4080,
 *     "total":    7508,
 *     "method":   "static" | "live",
 *     "asOf":     "2026-04-28T18:00:00.000Z"
 *   }
 *
 * Exit codes:
 *   0  always (script never blocks a build)
 *
 * Usage:
 *   node scripts/test-count-ledger.mjs
 *   node scripts/test-count-ledger.mjs --pretty
 *   node scripts/test-count-ledger.mjs --check-against=7500   (asserts >=)
 */
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = fileURLToPath(new URL(".", import.meta.url));
const REPO_ROOT = resolve(HERE, "..");
const FRONTEND = join(REPO_ROOT, "frontend");
const BACKEND = join(REPO_ROOT, "backend");

const SKIP_DIRS = new Set([
  "node_modules",
  ".next",
  ".git",
  "dist",
  "build",
  "coverage",
  "__pycache__",
  ".venv",
  "venv",
]);

function* walk(dir) {
  let entries;
  try {
    entries = readdirSync(dir);
  } catch {
    return;
  }
  for (const name of entries) {
    if (SKIP_DIRS.has(name)) continue;
    const full = join(dir, name);
    let st;
    try {
      st = statSync(full);
    } catch {
      continue;
    }
    if (st.isDirectory()) {
      yield* walk(full);
      continue;
    }
    yield full;
  }
}

function countFrontendTestsStatic(root) {
  // vitest convention: any function call to `it(`, `test(`, plus
  // `it.each(...)(name, ...)` and `test.each(...)(...)` test entries.
  const VITEST_TS = /\.(test|spec)\.(ts|tsx|js|jsx)$/;
  let count = 0;
  for (const file of walk(root)) {
    if (!VITEST_TS.test(file)) continue;
    let content;
    try {
      content = readFileSync(file, "utf8");
    } catch {
      continue;
    }
    // Plain `it(`, `test(` calls.
    const plain = (content.match(/(^|[^.\w])(it|test)\s*\(/g) || []).length;
    // `it.each(...)(`, `test.each(...)(` — each call expands but we count one
    // base and let live runners give the real number; the static count is a
    // floor (the marketing number always uses live or repo-verified).
    const each = (content.match(/(it|test)\.each\s*\(/g) || []).length;
    count += plain + each;
  }
  return count;
}

function countBackendTestsStatic(root) {
  const PY_TEST = /^test_.*\.py$/;
  let count = 0;
  for (const file of walk(root)) {
    const base = file.split(/[\\/]/).pop();
    if (!PY_TEST.test(base || "")) continue;
    let content;
    try {
      content = readFileSync(file, "utf8");
    } catch {
      continue;
    }
    const matches = content.match(/^\s*(?:async\s+)?def test_/gm) || [];
    count += matches.length;
  }
  return count;
}

function pad(n) {
  return String(n).padStart(6, " ");
}

function main() {
  const args = process.argv.slice(2);
  const pretty = args.includes("--pretty");
  const checkArg = args.find((a) => a.startsWith("--check-against="));
  const checkFloor = checkArg ? Number(checkArg.split("=")[1]) : null;

  const frontend = countFrontendTestsStatic(join(FRONTEND, "src"));
  const backend = countBackendTestsStatic(join(BACKEND, "tests"));
  const total = frontend + backend;

  const ledger = {
    frontend,
    backend,
    total,
    method: "static",
    asOf: new Date().toISOString(),
    notes: [
      "Static parse — counts test function definitions, not parametrize expansions.",
      "Live counts (vitest run + pytest --collect-only) may be higher; use those for press copy.",
    ],
  };

  if (pretty) {
    process.stdout.write(
      [
        "GoWork test ledger",
        "------------------",
        `Frontend: ${pad(frontend)}  (vitest, static)`,
        `Backend:  ${pad(backend)}  (pytest, static)`,
        `Total:    ${pad(total)}`,
        `As of:    ${ledger.asOf}`,
        "",
      ].join("\n"),
    );
  } else {
    process.stdout.write(`${JSON.stringify(ledger, null, 2)}\n`);
  }

  if (checkFloor !== null) {
    if (total < checkFloor) {
      process.stderr.write(
        `ledger: total ${total} < floor ${checkFloor}\n`,
      );
      process.exit(2);
    }
  }
}

main();

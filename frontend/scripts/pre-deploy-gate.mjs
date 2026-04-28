#!/usr/bin/env node
/**
 * W5 Driver C — Spotlight invention #1: pre-deploy-gate.mjs
 *
 * One-command runbook: from a clean checkout, runs the FULL submission
 * gauntlet. Exits 0 iff every gate is green.
 *
 * Invocation:
 *   cd frontend
 *   npm run pre-deploy
 *
 * Gates run, in order:
 *   1. tsc --noEmit                  (types)
 *   2. next lint                     (lint, accessibility, react-hooks)
 *   3. vitest run                    (3,400+ unit/integration tests)
 *   4. next build                    (production build, must exit 0)
 *   5. bpsai-pair arch check         (file/function/import limits)
 *   6. audit:brand                   (zero legacy-brand leaks)
 *   7. audit:tokens                  (zero hard-coded colors)
 *   8. contrast                      (AAA pairs intact)
 *   9. lhci autorun                  (Lighthouse, all 4 ≥ 0.90)
 *
 * Each gate's stdout/stderr is streamed live so a CI watcher can tail
 * the failure point. On the first non-zero exit, the script prints a
 * red banner and exits with the same code.
 *
 * Honest uncertainty: this script is the operator-facing aggregator;
 * the underlying commands carry the actual gate logic. If a gate's
 * underlying command is updated (e.g., we move from npx tsc to
 * tsgo), update this script in lockstep.
 */
import { spawnSync } from "node:child_process";
import process from "node:process";

/** Each gate is [label, executable, ...args]. Executed in sequence. */
const GATES = [
  ["TypeScript types", "npx", ["tsc", "--noEmit"]],
  ["Lint (next lint)", "npx", ["next", "lint"]],
  ["Vitest (3,400+ tests)", "npx", ["vitest", "run"]],
  ["Production build", "npm", ["run", "build"]],
  ["Architecture (bpsai-pair arch check)", "bpsai-pair", ["arch", "check", "frontend/"]],
  ["Brand audit (audit:brand)", "npm", ["run", "audit:brand"]],
  ["Token audit (audit:tokens)", "npm", ["run", "audit:tokens"]],
  ["Contrast (verify-contrast)", "npm", ["run", "contrast"]],
  ["Lighthouse (lhci autorun)", "npm", ["run", "lhci"]],
];

/**
 * Banner formatter — distinct from prose so a human eye spots the boundary
 * between the runbook output and the gate's own stdout.
 */
function banner(text, char = "=") {
  const line = char.repeat(72);
  console.log(`\n${line}\n${text}\n${line}`);
}

function runGate([label, cmd, args]) {
  banner(`▶ ${label}\n  $ ${cmd} ${args.join(" ")}`);
  const result = spawnSync(cmd, args, {
    stdio: "inherit",
    shell: process.platform === "win32",
  });
  if (result.error) {
    banner(`✗ ${label} — ERROR: ${result.error.message}`, "!");
    return result.status ?? 1;
  }
  if (result.status !== 0) {
    banner(`✗ ${label} — exit ${result.status}`, "!");
    return result.status ?? 1;
  }
  banner(`✓ ${label} — green`, "-");
  return 0;
}

function main() {
  const startedAt = Date.now();
  banner("GoWork pre-deploy gauntlet — every gate must be green to ship");
  for (const gate of GATES) {
    const code = runGate(gate);
    if (code !== 0) {
      const elapsedSec = Math.round((Date.now() - startedAt) / 1000);
      banner(
        `STOP: gate "${gate[0]}" failed after ${elapsedSec}s. Fix and rerun.`,
        "X",
      );
      process.exit(code);
    }
  }
  const elapsedSec = Math.round((Date.now() - startedAt) / 1000);
  banner(`ALL GATES GREEN in ${elapsedSec}s — clear to deploy.`);
  process.exit(0);
}

main();

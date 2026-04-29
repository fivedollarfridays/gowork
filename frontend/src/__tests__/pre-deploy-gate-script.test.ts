/**
 * W5 Driver C — Spotlight invention #1 contract.
 *
 * Pin the contract of `frontend/scripts/pre-deploy-gate.mjs`:
 *   - Script exists
 *   - Exposes a `npm run pre-deploy` command (in package.json scripts)
 *   - Runs the full gauntlet (tsc, lint, vitest, build, arch, brand,
 *     tokens, contrast, lhci) in sequence
 *   - Exits non-zero on any gate failure
 *
 * The script is the operator-facing one-command runbook: from a clean
 * checkout, `npm run pre-deploy` returns 0 iff every submission gate is
 * green. The contract is a list-of-gates (not implementation details);
 * the script's stdout is the audit trail.
 */
import { describe, it, expect } from "vitest";
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

const SCRIPT_PATH = join(
  process.cwd(),
  "scripts",
  "pre-deploy-gate.mjs",
);
const PACKAGE_JSON_PATH = join(process.cwd(), "package.json");

describe("scripts/pre-deploy-gate.mjs — Spotlight #1", () => {
  it("exists at the expected path", () => {
    expect(existsSync(SCRIPT_PATH)).toBe(true);
  });

  const src = existsSync(SCRIPT_PATH) ? readFileSync(SCRIPT_PATH, "utf8") : "";

  it("declares each required gate by name in stdout / comments", () => {
    expect(src).toMatch(/tsc/);
    expect(src).toMatch(/lint/i);
    expect(src).toMatch(/vitest/);
    expect(src).toMatch(/build/i);
    expect(src).toMatch(/audit:brand|brand audit/i);
    expect(src).toMatch(/audit:tokens|token audit/i);
    expect(src).toMatch(/contrast/i);
    expect(src).toMatch(/lhci|[Ll]ighthouse/);
  });

  it("uses Node child_process to run sub-commands (deterministic)", () => {
    expect(src).toMatch(/spawnSync|execSync|child_process/);
  });

  it("exits non-zero on failure", () => {
    expect(src).toMatch(
      /process\.exit\(\s*(?:1|code|status)\s*\)|process\.exitCode|exit code/i,
    );
  });

  it("uses ES modules (.mjs convention)", () => {
    // Either `import ... from` or `export ` — should not look like a CJS file.
    expect(src).toMatch(/import .+ from/);
  });

  it("is registered in package.json scripts as `pre-deploy`", () => {
    const pkg = JSON.parse(readFileSync(PACKAGE_JSON_PATH, "utf8"));
    expect(pkg.scripts["pre-deploy"]).toBeTypeOf("string");
    expect(pkg.scripts["pre-deploy"]).toMatch(/pre-deploy-gate\.mjs/);
  });
});

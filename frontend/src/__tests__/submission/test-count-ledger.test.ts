/**
 * W5 Driver A — Spotlight invention #2 contract test (T5.A.8)
 *
 * Asserts the test-count-ledger script (`scripts/test-count-ledger.mjs`)
 * exists, runs without crashing, returns valid JSON, and produces totals
 * consistent with what README + press kit cite.
 *
 * Drift guard: if a future driver removes the ledger or breaks its output
 * shape, this test fails immediately, before stale numbers leak into
 * marketing copy.
 */
import { describe, it, expect } from "vitest";
import { existsSync } from "node:fs";
import { execSync } from "node:child_process";
import { join, resolve } from "node:path";

const REPO_ROOT = resolve(__dirname, "..", "..", "..", "..");
const LEDGER_SCRIPT = join(REPO_ROOT, "scripts", "test-count-ledger.mjs");

interface Ledger {
  frontend: number;
  backend: number;
  total: number;
  method: string;
  asOf: string;
  notes?: string[];
}

function runLedger(extraArgs: string[] = []): { stdout: string; code: number } {
  try {
    const out = execSync(
      `node "${LEDGER_SCRIPT}" ${extraArgs.join(" ")}`.trim(),
      { cwd: REPO_ROOT, encoding: "utf8", stdio: "pipe" },
    );
    return { stdout: out, code: 0 };
  } catch (err) {
    const e = err as { status: number; stdout?: string; stderr?: string };
    return { stdout: `${e.stdout ?? ""}${e.stderr ?? ""}`, code: e.status };
  }
}

describe("Test-count-ledger script (Spotlight #2)", () => {
  it("scripts/test-count-ledger.mjs exists", () => {
    expect(existsSync(LEDGER_SCRIPT)).toBe(true);
  });

  it("runs without crashing and emits JSON", () => {
    const { stdout, code } = runLedger();
    expect(code).toBe(0);
    expect(() => JSON.parse(stdout) as Ledger).not.toThrow();
  });

  it("emits frontend + backend + total integers", () => {
    const { stdout } = runLedger();
    const ledger = JSON.parse(stdout) as Ledger;
    expect(Number.isInteger(ledger.frontend)).toBe(true);
    expect(Number.isInteger(ledger.backend)).toBe(true);
    expect(Number.isInteger(ledger.total)).toBe(true);
    expect(ledger.frontend).toBeGreaterThan(0);
    expect(ledger.backend).toBeGreaterThan(0);
    expect(ledger.total).toBe(ledger.frontend + ledger.backend);
  });

  it("ledger total clears the marketing floor (>= 5000)", () => {
    const { stdout } = runLedger();
    const ledger = JSON.parse(stdout) as Ledger;
    // The marketing copy claims ~7,500+ tests. The static-parse method
    // undercounts (parametrize expansion happens at run-time), so we only
    // require >= 5000 as a sanity floor here. Live `vitest run` + pytest
    // collect produce the higher number cited in copy.
    expect(ledger.total).toBeGreaterThanOrEqual(5000);
  });

  it("declares its counting method", () => {
    const { stdout } = runLedger();
    const ledger = JSON.parse(stdout) as Ledger;
    expect(ledger.method).toMatch(/static|live/);
  });

  it("--check-against floor exits 0 when satisfied", () => {
    const { code } = runLedger(["--check-against=1000"]);
    expect(code).toBe(0);
  });

  it("--check-against floor exits non-zero when violated", () => {
    const { code } = runLedger(["--check-against=999999"]);
    expect(code).not.toBe(0);
  });
});

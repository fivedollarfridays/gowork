/**
 * Wave 5 — tooling: audit scripts run clean.
 *
 * Brand-integrity sweep + token-usage audit must pass on the current
 * sprint/w1-foundation tree.
 */
import { describe, it, expect } from "vitest";
import { execSync } from "node:child_process";
import { join } from "node:path";

const HERE = process.cwd();
const BRAND = join(HERE, "scripts", "audit-brand-integrity.mjs");
const TOKENS = join(HERE, "scripts", "audit-tokens.mjs");

function runScript(path: string): { code: number; out: string } {
  let out = "";
  let code = 0;
  try {
    out = execSync(`node "${path}"`, {
      cwd: HERE,
      encoding: "utf8",
      stdio: "pipe",
    });
  } catch (err) {
    const e = err as { status: number; stdout?: string; stderr?: string };
    code = e.status;
    out = `${e.stdout ?? ""}\n${e.stderr ?? ""}`;
  }
  return { code, out };
}

describe("scripts/audit-brand-integrity.mjs", () => {
  it("exits 0 (clean) on the current tree", () => {
    const { code, out } = runScript(BRAND);
    expect(code).toBe(0);
    expect(out).toMatch(/OK|brand chrome clean/);
  });

  it("npm run audit:brand is registered", () => {
    const pkg = JSON.parse(
      execSync("node -e \"console.log(require('fs').readFileSync('package.json','utf8'))\"", {
        cwd: HERE,
        encoding: "utf8",
      }),
    ) as { scripts: Record<string, string> };
    expect(pkg.scripts["audit:brand"]).toBeDefined();
  });
});

describe("scripts/audit-tokens.mjs", () => {
  it("exits 0 — no var() consumers without a declaration", () => {
    const { code, out } = runScript(TOKENS);
    expect(code).toBe(0);
    expect(out).not.toMatch(/HARD:/);
  });

  it("npm run audit:tokens is registered", () => {
    const pkg = JSON.parse(
      execSync("node -e \"console.log(require('fs').readFileSync('package.json','utf8'))\"", {
        cwd: HERE,
        encoding: "utf8",
      }),
    ) as { scripts: Record<string, string> };
    expect(pkg.scripts["audit:tokens"]).toBeDefined();
  });
});

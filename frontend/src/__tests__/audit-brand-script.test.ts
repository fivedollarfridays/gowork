/**
 * audit-legacy-brand.mjs runs clean on current state (T1.77).
 *
 * The script exits non-zero if any unexpected legacy MontGoWork / M-shape
 * reference appears in source code or public assets. This test is the
 * gate that proves the retirement is complete.
 */
import { describe, it, expect } from "vitest";
import { execSync } from "node:child_process";
import { join } from "node:path";

const SCRIPT = join(process.cwd(), "scripts", "audit-legacy-brand.mjs");

describe("scripts/audit-legacy-brand.mjs", () => {
  it("runs clean (exit 0) on the current sprint/w1-foundation tree", () => {
    let result = "";
    let exitCode = 0;
    try {
      result = execSync(`node "${SCRIPT}"`, {
        cwd: process.cwd(),
        encoding: "utf8",
        stdio: "pipe",
      });
    } catch (err) {
      const e = err as { status: number; stdout?: string; stderr?: string };
      exitCode = e.status;
      result = `${e.stdout ?? ""}\n${e.stderr ?? ""}`;
    }
    expect(exitCode).toBe(0);
    expect(result).toMatch(/OK/);
  });

  it("npm run audit:brand script is registered in package.json", () => {
    const pkg = JSON.parse(
      execSync("node -e \"console.log(require('fs').readFileSync('package.json','utf8'))\"", {
        cwd: process.cwd(),
        encoding: "utf8",
      }),
    ) as { scripts: Record<string, string> };
    expect(pkg.scripts["audit:brand"]).toBeDefined();
    expect(pkg.scripts["audit:brand"]).toMatch(/audit-legacy-brand|audit-brand/);
  });
});

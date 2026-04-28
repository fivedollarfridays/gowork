/**
 * W4 Driver C — T4.C.2 — WCAG AAA contrast gate (vitest-driven).
 *
 * The CLI shim `npm run contrast` already runs the same library; this
 * test wires it into the vitest run so a contrast regression fails
 * the suite (not just the standalone audit). Without this, a careless
 * token change can ship to a PR that's vitest-green but contrast-red.
 */
import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { runContrastReport } from "../../scripts/lib/contrast.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const COLORS_CSS = resolve(
  HERE,
  "..",
  "app",
  "styles",
  "tokens",
  "colors.css",
);

describe("T4.C.2 — WCAG AAA contrast gate (vitest)", () => {
  it("the live colors.css passes WCAG AAA across every fg/bg pair", () => {
    const css = readFileSync(COLORS_CSS, "utf-8");
    const report = runContrastReport(css);

    if (!report.ok) {
      // Surface the failing pairs so the diff is obvious in CI logs.
      // The contrast script's own report includes this line for line.
      const summary = report.failures.map((f) => f.line).join("\n");
      throw new Error(`AAA contrast failures :\n${summary}`);
    }
    expect(report.ok).toBe(true);
    expect(report.failures.length).toBe(0);
  });

  it("at least 15 pairs are checked (sanity — palette didn't shrink)", () => {
    const css = readFileSync(COLORS_CSS, "utf-8");
    const report = runContrastReport(css);
    expect(report.results.length).toBeGreaterThanOrEqual(15);
  });

  it("primary text on every surface (--bg-base/surface/elevated) clears AAA-normal (>=7:1)", () => {
    const css = readFileSync(COLORS_CSS, "utf-8");
    const report = runContrastReport(css);
    const primaryPairs = report.results.filter(
      (r) => r.fg === "--fg-primary" && r.weight === "normal",
    );
    expect(primaryPairs.length).toBe(3); // base + surface + elevated
    for (const p of primaryPairs) {
      expect(p.ratio).toBeGreaterThanOrEqual(7);
    }
  });
});

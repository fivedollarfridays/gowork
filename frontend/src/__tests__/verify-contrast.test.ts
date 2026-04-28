import { describe, it, expect } from "vitest";
import {
  parseHexTokens,
  contrastRatio,
  classifyPair,
  buildPairsToCheck,
  runContrastReport,
  // The library is shipped as a plain .mjs so the CLI shim
  // (scripts/verify-contrast.mjs) can `import "./lib/contrast.mjs"` without
  // a TypeScript loader. Vitest still type-checks via JSDoc declarations.
} from "../../scripts/lib/contrast.mjs";

/**
 * T1.13 — WCAG AAA contrast script (extracted into a testable lib).
 *
 * The CLI shim (frontend/scripts/verify-contrast.mjs) is a thin entry that
 * imports this lib. The lib is shipped as a TS module so vitest can drive it
 * without spawning Node subprocesses.
 *
 * AAA thresholds:
 *   - Normal text >= 7.0 : 1
 *   - Large text  >= 4.5 : 1
 *   - UI graphics (focus rings) >= 3.0 : 1
 */

describe("T1.13 — hex token parser", () => {
  it("extracts hex tokens from a CSS string", () => {
    const css = `:root {
      --bg-base: #0A0E1A;
      --fg-primary: #F5F3EE;
      --accent-cyan: #22D3EE;
      --bg-glass: rgba(255,255,255,0.04);
    }`;
    const tokens = parseHexTokens(css);
    expect(tokens.get("--bg-base")).toBe("#0A0E1A");
    expect(tokens.get("--fg-primary")).toBe("#F5F3EE");
    expect(tokens.get("--accent-cyan")).toBe("#22D3EE");
  });

  it("ignores rgba() and color-mix() (only literal hex captured)", () => {
    const css = `--bg-glass: rgba(255,255,255,0.04); --x: color-mix(in oklch, white, black);`;
    const tokens = parseHexTokens(css);
    expect(tokens.has("--bg-glass")).toBe(false);
    expect(tokens.has("--x")).toBe(false);
  });
});

describe("T1.13 — contrastRatio (WCAG 2.x relative luminance)", () => {
  it("white on black is 21:1 (the maximum)", () => {
    const r = contrastRatio("#FFFFFF", "#000000");
    expect(r).toBeCloseTo(21, 0);
  });

  it("black on black is 1:1", () => {
    expect(contrastRatio("#000000", "#000000")).toBeCloseTo(1, 1);
  });

  it("--fg-primary (#F5F3EE) on --bg-base (#0A0E1A) clears AAA normal (>=7)", () => {
    const r = contrastRatio("#F5F3EE", "#0A0E1A");
    expect(r).toBeGreaterThanOrEqual(7);
  });

  it("--accent-cyan (#22D3EE) on --bg-base (#0A0E1A) clears UI-3:1", () => {
    const r = contrastRatio("#22D3EE", "#0A0E1A");
    expect(r).toBeGreaterThanOrEqual(3);
  });
});

describe("T1.13 — classifyPair", () => {
  it("classifies normal text >=7 as PASS", () => {
    expect(classifyPair(7.5, "normal").pass).toBe(true);
  });
  it("classifies normal text 6.9 as FAIL", () => {
    expect(classifyPair(6.9, "normal").pass).toBe(false);
  });
  it("classifies large text >=4.5 as PASS", () => {
    expect(classifyPair(4.6, "large").pass).toBe(true);
  });
  it("classifies UI graphics >=3 as PASS", () => {
    expect(classifyPair(3.0, "ui").pass).toBe(true);
  });
});

describe("T1.13 — buildPairsToCheck", () => {
  it("emits all critical pairs for the W1 base palette", () => {
    const tokens = new Map([
      ["--bg-base", "#0A0E1A"],
      ["--bg-surface", "#0F1729"],
      ["--bg-elevated", "#1A2338"],
      ["--fg-primary", "#F5F3EE"],
      ["--fg-secondary", "#94A3B8"],
      ["--fg-muted", "#64748B"],
      ["--accent-cyan", "#22D3EE"],
      ["--accent-amber", "#F59E0B"],
      ["--status-positive", "#34D399"],
    ]);
    const pairs = buildPairsToCheck(tokens);
    expect(pairs.length).toBeGreaterThanOrEqual(10);
    const names = pairs.map((p) => `${p.fg} on ${p.bg}`);
    expect(names).toContain("--fg-primary on --bg-base");
    expect(names).toContain("--accent-cyan on --bg-base");
  });
});

describe("T1.13 — runContrastReport (integration)", () => {
  const validCss = `:root {
    --bg-base: #0A0E1A;
    --bg-surface: #0F1729;
    --bg-elevated: #1A2338;
    --fg-primary: #F5F3EE;
    --fg-secondary: #A4B3C7;
    --fg-muted: #8696A8;
    --accent-cyan: #22D3EE;
    --accent-amber: #F59E0B;
    --status-positive: #34D399;
  }`;

  it("returns ok=true for the W1 base palette", () => {
    const report = runContrastReport(validCss);
    expect(report.ok).toBe(true);
    expect(report.failures.length).toBe(0);
    expect(report.results.length).toBeGreaterThan(0);
  });

  it("returns ok=false when a deliberately bad pair is present", () => {
    const badCss = `:root { --bg-base: #444444; --fg-primary: #555555; }`;
    const report = runContrastReport(badCss);
    expect(report.ok).toBe(false);
    expect(report.failures.length).toBeGreaterThan(0);
  });

  it("each result line includes computed ratio with 1-decimal precision", () => {
    const report = runContrastReport(validCss);
    for (const r of report.results) {
      expect(r.line).toMatch(/\d+\.\d:1/);
    }
  });
});

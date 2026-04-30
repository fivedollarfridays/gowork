import { describe, it, expect } from "vitest";
import fs from "fs";
import path from "path";

/**
 * T1.15 — Inter Variable + optical-size axis + metric-tuned fallback.
 *
 * Driver A scope (THIS task): the CSS-side tokens (--font-inter-var,
 * --font-inter-stack) that layout.tsx will consume.
 *
 * Driver C scope (deferred): the actual `next/font/google` Inter
 * configuration in layout.tsx with `axes: ['opsz']`, `weight: 'variable'`,
 * `adjustFontFallback: true`. Driver A does NOT modify layout.tsx per
 * dispatch file-ownership matrix; Driver C imports these tokens and wires
 * Inter Variable in the layout rewrite.
 */

const FRONTEND_ROOT = path.resolve(__dirname, "..", "..");
const TYPOGRAPHY_CSS = path.resolve(FRONTEND_ROOT, "src/app/styles/tokens/typography.css");

function read(): string {
  return fs.readFileSync(TYPOGRAPHY_CSS, "utf-8");
}

describe("T1.15 — Inter Variable token surface (CSS)", () => {
  const css = read();

  it("defines --font-inter-var as a passthrough for the next/font CSS variable", () => {
    expect(css).toMatch(/--font-inter-var\s*:\s*var\(--font-inter\)/);
  });

  it("defines --font-inter-stack with metric-tuned fallback chain", () => {
    expect(css).toMatch(/--font-inter-stack\s*:/);
    // Stack must include at least 4 fallback families for CLS budget protection.
    const stackMatch = css.match(/--font-inter-stack\s*:\s*([^;]+);/);
    expect(stackMatch, "stack token must be present").not.toBeNull();
    const stack = stackMatch![1];
    const families = stack.split(",").map((s) => s.trim());
    expect(families.length).toBeGreaterThanOrEqual(5);
    expect(stack).toMatch(/--font-inter-var/);
    expect(stack).toMatch(/-apple-system/);
    expect(stack).toMatch(/sans-serif$/);
  });

  it("documents the Driver C handoff for layout.tsx Inter Variable wiring", () => {
    // The CSS file must surface a comment pointing at the deferred work so
    // the reviewer (and Driver C) sees the intentional separation.
    expect(css).toMatch(/Driver C|layout\.tsx/);
    expect(css).toMatch(/opsz|optical[- ]size/i);
  });
});

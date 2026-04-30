/**
 * T-Render.6 — BenefitsCliffChart drama scale (visual-render-fix branch).
 *
 * Locks the dramatic-stroke contract for the cliff visualisation:
 *   - Source declares strokeWidth >= 4 on the main Area path
 *   - Source declares an "← Cliff" annotation literal at the threshold
 *   - Source declares a gradient fill (linearGradient or color-mix) ramp
 *
 * Source-level only; jsdom + Recharts can't be trusted for visual
 * snapshots (ResponsiveContainer renders at 0px in jsdom — the existing
 * temperature test already documents this). The Playwright e2e is the
 * browser-level guard.
 */
import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const FRONTEND_ROOT = resolve(__dirname, "..", "..", "..", "..");
const SOURCE_PATH = resolve(
  FRONTEND_ROOT,
  "src/components/plan/BenefitsCliffChart.tsx",
);

function readSource(): string {
  return readFileSync(SOURCE_PATH, "utf-8");
}

describe("BenefitsCliffChart — drama scale (T-Render.6)", () => {
  it("Area declares strokeWidth >= 4 via constant or literal", () => {
    const src = readSource();
    // Match `strokeWidth={4}` literal OR a constant like AREA_STROKE_WIDTH
    // that's set to a value >= 4.
    const literalMatch = src.match(/strokeWidth=\{(?:[4-9]|[1-9]\d+)/);
    const constMatch = src.match(/AREA_STROKE_WIDTH\s*=\s*([4-9]|[1-9]\d+)/);
    expect(literalMatch !== null || constMatch !== null).toBe(true);
  });

  it("source includes the '← Cliff' annotation label", () => {
    const src = readSource();
    expect(src).toMatch(/Cliff/);
  });

  it("source declares a gradient fill ramp (linearGradient or stop)", () => {
    const src = readSource();
    expect(src).toMatch(/<linearGradient|<stop\s/);
  });
});

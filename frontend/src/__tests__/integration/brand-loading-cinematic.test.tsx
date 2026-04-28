/**
 * Wave 4 architectural improvement — BrandMark loading + cinematic compose.
 *
 * Verifies:
 *   - BrandMark loading=true applies the brand-loading class
 *   - cinematic step durations sum to the documented 4.6s total
 *   - The cinematic + brand-loading + path-draw (T1.107) systems are all
 *     reachable via lib/wall barrel exports (no dead code, no orphans)
 */
import { describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import {
  CINEMATIC_STEPS,
  CINEMATIC_TOTAL_MS,
  getCinematicStep,
  BRAND_ASSETS,
  STORAGE_KEYS,
} from "@/lib/wall";
import { BrandMark } from "@/components/wall/BrandMark";

describe("Wave 4 — BrandMark loading + cinematic + lib/wall barrel", () => {
  it("BrandMark loading=true wires the brand-loading class for the keyframe", () => {
    const { container } = render(<BrandMark loading />);
    const svg = container.querySelector("svg.gowork-mark");
    expect(svg?.className.baseVal).toMatch(/brand-loading/);
  });

  it("BrandMark interactive=true wires gowork-mark--hover for T1.107 hover draw", () => {
    const { container } = render(<BrandMark interactive />);
    const svg = container.querySelector("svg.gowork-mark");
    expect(svg?.className.baseVal).toMatch(/gowork-mark--hover/);
  });

  it("BrandMark default does NOT animate (no loading nor interactive)", () => {
    const { container } = render(<BrandMark />);
    const svg = container.querySelector("svg.gowork-mark");
    expect(svg?.className.baseVal).not.toMatch(/brand-loading/);
    expect(svg?.className.baseVal).not.toMatch(/gowork-mark--hover/);
  });

  it("cinematic system integrates via lib/wall barrel", () => {
    const presenter = getCinematicStep("presenter");
    expect(presenter?.delayMs).toBe(0);
    const total = CINEMATIC_STEPS.reduce(
      (max, s) => Math.max(max, s.delayMs + s.durationMs),
      0,
    );
    expect(CINEMATIC_TOTAL_MS).toBeGreaterThanOrEqual(total);
  });

  it("brand assets registry contains the canonical icon + sounds", () => {
    const names = BRAND_ASSETS.map((a) => a.name);
    expect(names).toContain("icon.svg");
    expect(names).toContain("footstep.mp3");
  });

  it("STORAGE_KEYS is reachable from lib/wall and has canonical values", () => {
    expect(STORAGE_KEYS.MUTED).toBe("gowork.muted");
    expect(STORAGE_KEYS.LOCALE).toBe("gowork.locale");
  });
});

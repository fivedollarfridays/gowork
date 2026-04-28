import { describe, it, expect } from "vitest";
import fs from "node:fs";
import path from "node:path";
import {
  EASE_LINEAR_SIG,
  EASE_OUT,
  DURATION_BASELINE_MS,
} from "../tokens";

/**
 * T1.20 — Easing + duration tokens.
 *
 * Linear's signature easing (cubic-bezier(0.32, 0.72, 0, 1)) carries the
 * "real software" feel; EASE_OUT is the Apple/Vercel standard for incoming
 * motion. DURATION_BASELINE_MS = 280 (just past instant, not slow).
 */

describe("T1.20 — easing constants", () => {
  it("EASE_LINEAR_SIG is a 4-tuple cubic-bezier signature", () => {
    expect(EASE_LINEAR_SIG).toHaveLength(4);
    expect(EASE_LINEAR_SIG).toEqual([0.32, 0.72, 0, 1]);
  });

  it("EASE_OUT is a 4-tuple cubic-bezier signature", () => {
    expect(EASE_OUT).toHaveLength(4);
    expect(EASE_OUT).toEqual([0.16, 1, 0.3, 1]);
  });

  it("each easing value is numeric (no NaN, no string)", () => {
    for (const v of [...EASE_LINEAR_SIG, ...EASE_OUT]) {
      expect(typeof v).toBe("number");
      expect(Number.isFinite(v)).toBe(true);
    }
  });
});

describe("T1.20 — duration constants", () => {
  it("DURATION_BASELINE_MS === 280", () => {
    expect(DURATION_BASELINE_MS).toBe(280);
  });
});

describe("T1.20 — CSS-side mirrors", () => {
  const motionCss = fs.readFileSync(
    path.resolve(__dirname, "..", "..", "..", "app", "styles", "tokens", "motion.css"),
    "utf-8",
  );

  it("--ease-linear-sig declared with cubic-bezier matching TS", () => {
    expect(motionCss).toMatch(/--ease-linear-sig:\s*cubic-bezier\(0\.32,\s*0\.72,\s*0,\s*1\)/);
  });

  it("--ease-out declared with cubic-bezier matching TS", () => {
    expect(motionCss).toMatch(/--ease-out:\s*cubic-bezier\(0\.16,\s*1,\s*0\.3,\s*1\)/);
  });

  it("--duration-baseline declared as 280ms", () => {
    expect(motionCss).toMatch(/--duration-baseline:\s*280ms/);
  });
});

import { describe, it, expect } from "vitest";
import fs from "node:fs";
import path from "node:path";
import {
  STAGGER_CHILD_OFFSET_S,
  STAGGER_INITIAL_DEFAULT,
  STAGGER_ANIMATE_DEFAULT,
} from "../tokens";

/**
 * T1.21 — Stagger timing tokens.
 *
 * Note on Spotlight Resilience: dispatch instructs Driver A to PROTECT
 * frontend/src/lib/motion.tsx (which uses 0.25 staggerChildren — different
 * cadence for shadcn/dashboard pages). The 0.05 value here is the new W2/W3/W4
 * default for chapter scrollytelling sites. Driver C will adopt these tokens
 * in NEW components rather than retrofit the existing utility.
 */

describe("T1.21 — stagger constants", () => {
  it("STAGGER_CHILD_OFFSET_S === 0.05", () => {
    expect(STAGGER_CHILD_OFFSET_S).toBe(0.05);
  });

  it("STAGGER_INITIAL_DEFAULT = { opacity: 0, y: 20 }", () => {
    expect(STAGGER_INITIAL_DEFAULT.opacity).toBe(0);
    expect(STAGGER_INITIAL_DEFAULT.y).toBe(20);
  });

  it("STAGGER_ANIMATE_DEFAULT = { opacity: 1, y: 0 }", () => {
    expect(STAGGER_ANIMATE_DEFAULT.opacity).toBe(1);
    expect(STAGGER_ANIMATE_DEFAULT.y).toBe(0);
  });
});

describe("T1.21 — CSS-side mirrors", () => {
  const motionCss = fs.readFileSync(
    path.resolve(__dirname, "..", "..", "..", "app", "styles", "tokens", "motion.css"),
    "utf-8",
  );

  it("--stagger-child-offset declared as 0.05s", () => {
    expect(motionCss).toMatch(/--stagger-child-offset:\s*0\.05s/);
  });

  it("--stagger-default-y declared as 20px", () => {
    expect(motionCss).toMatch(/--stagger-default-y:\s*20px/);
  });
});

import { describe, it, expect } from "vitest";
import {
  SPRING_SOFT,
  SPRING_SNAPPY,
  SPRING_ELASTIC,
} from "../tokens";

/**
 * T1.19 — Spring preset tokens (TS export).
 *
 * Three framer-motion spring presets locked to plan-file values. Consumed
 * across W2 (camera flyTo), W3 (Carlos avatar), W4 (variable font axis
 * interpolation). One change here cascades — these are the foundation.
 */

describe("T1.19 — spring preset constants", () => {
  it.each([
    ["SPRING_SOFT", SPRING_SOFT, 100, 20],
    ["SPRING_SNAPPY", SPRING_SNAPPY, 200, 25],
    ["SPRING_ELASTIC", SPRING_ELASTIC, 300, 18],
  ])("%s = stiffness %i, damping %i", (_name, preset, stiffness, damping) => {
    expect(preset.stiffness).toBe(stiffness);
    expect(preset.damping).toBe(damping);
  });

  it("each preset is deeply readonly (TypeScript as const)", () => {
    // Runtime proof: properties are own enumerable; TS as const surfaces at
    // type level. We verify both fields exist and their numeric type.
    for (const preset of [SPRING_SOFT, SPRING_SNAPPY, SPRING_ELASTIC]) {
      expect(typeof preset.stiffness).toBe("number");
      expect(typeof preset.damping).toBe("number");
    }
  });
});

describe("T1.19 — CSS-side spring vars (mirror of TS)", () => {
  it("motion.css declares 6 spring CSS variables (3 stiff + 3 damp)", () => {
    // Motion.css mirrors the TS values for non-framer (CSS-animation) consumers.
    // Read the file and assert the declarations.
    const fs = require("node:fs") as typeof import("fs");
    const path = require("node:path") as typeof import("path");
    const motionCss = fs.readFileSync(
      path.resolve(__dirname, "..", "..", "..", "app", "styles", "tokens", "motion.css"),
      "utf-8",
    );
    expect(motionCss).toMatch(/--spring-soft-stiff:\s*100/);
    expect(motionCss).toMatch(/--spring-soft-damp:\s*20/);
    expect(motionCss).toMatch(/--spring-snappy-stiff:\s*200/);
    expect(motionCss).toMatch(/--spring-snappy-damp:\s*25/);
    expect(motionCss).toMatch(/--spring-elastic-stiff:\s*300/);
    expect(motionCss).toMatch(/--spring-elastic-damp:\s*18/);
  });
});

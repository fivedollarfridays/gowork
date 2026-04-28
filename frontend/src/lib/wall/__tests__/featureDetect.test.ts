/**
 * Spotlight invention 2 — feature-detect (lib/wall/featureDetect.ts).
 *
 * Centralizes browser feature detection that the wall scatters across
 * components (View Transitions, Battery, Vibration, container queries,
 * color-mix, OKLCH). Detections cache once at module load — no
 * per-render thrash — and are SSR-safe (return false on server).
 */
import { describe, it, expect } from "vitest";
import {
  hasViewTransitions,
  hasContainerQueries,
  hasColorMix,
  hasOklch,
  hasVibration,
  hasBatteryAPI,
  detectFeatures,
} from "../featureDetect";

describe("featureDetect — individual probes", () => {
  it("hasViewTransitions returns boolean", () => {
    expect(typeof hasViewTransitions()).toBe("boolean");
  });

  it("hasContainerQueries returns boolean", () => {
    expect(typeof hasContainerQueries()).toBe("boolean");
  });

  it("hasColorMix returns boolean", () => {
    expect(typeof hasColorMix()).toBe("boolean");
  });

  it("hasOklch returns boolean", () => {
    expect(typeof hasOklch()).toBe("boolean");
  });

  it("hasVibration returns boolean", () => {
    expect(typeof hasVibration()).toBe("boolean");
  });

  it("hasBatteryAPI returns boolean", () => {
    expect(typeof hasBatteryAPI()).toBe("boolean");
  });
});

describe("featureDetect — detectFeatures aggregate", () => {
  it("returns a flat object with every probe key", () => {
    const f = detectFeatures();
    expect(f).toHaveProperty("viewTransitions");
    expect(f).toHaveProperty("containerQueries");
    expect(f).toHaveProperty("colorMix");
    expect(f).toHaveProperty("oklch");
    expect(f).toHaveProperty("vibration");
    expect(f).toHaveProperty("batteryAPI");
  });

  it("every property is a boolean", () => {
    const f = detectFeatures();
    for (const v of Object.values(f)) expect(typeof v).toBe("boolean");
  });
});

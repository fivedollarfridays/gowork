/**
 * Spotlight invention 4 — first-paint cinematic token system.
 *
 * Codifies the 4-second TitleSequence + path-line + Mapbox-init choreography
 * as a structured set of step tokens (delay-from-start + duration + easing
 * + intent). Other surfaces (W2 chapter intros, edge-state transitions)
 * reach for the same vocabulary so timing stays coherent across the app.
 */
import { describe, it, expect } from "vitest";
import {
  CINEMATIC_STEPS,
  CINEMATIC_TOTAL_MS,
  getCinematicStep,
} from "../cinematic";

describe("cinematic — timing tokens", () => {
  it("declares the four canonical steps", () => {
    const ids = CINEMATIC_STEPS.map((s) => s.id);
    expect(ids).toEqual(
      expect.arrayContaining(["presenter", "title", "subtitle", "handoff"]),
    );
  });

  it("step delays are monotonic (each step starts at or after prior)", () => {
    let last = -1;
    for (const step of CINEMATIC_STEPS) {
      expect(step.delayMs).toBeGreaterThanOrEqual(last);
      last = step.delayMs;
    }
  });

  it("each step has a positive duration", () => {
    for (const step of CINEMATIC_STEPS) {
      expect(step.durationMs).toBeGreaterThan(0);
    }
  });

  it("each step has a token easing string consumable by CSS / framer", () => {
    for (const step of CINEMATIC_STEPS) {
      expect(step.easing).toMatch(/^cubic-bezier|^ease|^var\(/);
    }
  });

  it("CINEMATIC_TOTAL_MS bounds the longest step", () => {
    const last = CINEMATIC_STEPS[CINEMATIC_STEPS.length - 1];
    expect(CINEMATIC_TOTAL_MS).toBeGreaterThanOrEqual(
      last.delayMs + last.durationMs,
    );
  });

  it("getCinematicStep('title') returns the title-text step", () => {
    const step = getCinematicStep("title");
    expect(step?.id).toBe("title");
  });
});

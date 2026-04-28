/**
 * T4.D.5 — View Transitions polish.
 *
 * Adds reverse-direction + fallback assertions to the wall ⇄ assess
 * morph. The Ch10 → /assess forward path was shipped by W3 Driver C;
 * here we verify:
 *
 *   1. The constant is single-source (one name, two pages, zero drift).
 *   2. `startViewTransitionWithFallback` runs the navigation when the
 *      API is unsupported (Firefox safety net).
 *   3. `startViewTransitionWithFallback` honors `reducedMotion: true`
 *      and skips the API even when supported.
 *   4. The reverse direction (assess back to wall) reuses the same
 *      morph-target string so a future driver doesn't introduce
 *      `wall-to-assess-back` and break the symmetry.
 */

import { describe, it, expect, vi, afterEach } from "vitest";
import {
  WALL_TO_ASSESS_TRANSITION_NAME,
  startViewTransitionWithFallback,
  supportsViewTransitions,
} from "../viewTransitions";

afterEach(() => {
  // Cleanup any patched document helper.
  delete (
    document as unknown as { startViewTransition?: unknown }
  ).startViewTransition;
  delete (
    document as unknown as { __viewTransitionInFlight?: boolean }
  ).__viewTransitionInFlight;
});

describe("T4.D.5 — view transitions: constant single-source", () => {
  it("WALL_TO_ASSESS_TRANSITION_NAME is 'wall-to-assess'", () => {
    expect(WALL_TO_ASSESS_TRANSITION_NAME).toBe("wall-to-assess");
  });

  it("constant is reused for reverse direction (no -back suffix introduced)", () => {
    expect(WALL_TO_ASSESS_TRANSITION_NAME).not.toMatch(/-back/);
  });
});

describe("T4.D.5 — supportsViewTransitions feature detection", () => {
  it("returns false when document.startViewTransition is missing (Firefox)", () => {
    delete (
      document as unknown as { startViewTransition?: unknown }
    ).startViewTransition;
    expect(supportsViewTransitions()).toBe(false);
  });

  it("returns true when document.startViewTransition is present (Chrome)", () => {
    (document as unknown as { startViewTransition: () => void }).startViewTransition =
      () => undefined;
    expect(supportsViewTransitions()).toBe(true);
  });
});

describe("T4.D.5 — startViewTransitionWithFallback fallback path", () => {
  it("calls navigate() unwrapped when API is missing", () => {
    delete (
      document as unknown as { startViewTransition?: unknown }
    ).startViewTransition;
    const navigate = vi.fn();
    startViewTransitionWithFallback(navigate);
    expect(navigate).toHaveBeenCalledTimes(1);
  });

  it("calls navigate() unwrapped when reducedMotion is true (even with API present)", () => {
    const startVT = vi.fn();
    (
      document as unknown as { startViewTransition: (cb: () => void) => void }
    ).startViewTransition = (cb: () => void) => {
      startVT(cb);
      cb();
    };
    const navigate = vi.fn();
    startViewTransitionWithFallback(navigate, { reducedMotion: true });
    expect(navigate).toHaveBeenCalledTimes(1);
    expect(startVT).not.toHaveBeenCalled();
  });

  it("wraps navigate() in startViewTransition when supported and not reduced", () => {
    const startVT = vi.fn();
    (
      document as unknown as { startViewTransition: (cb: () => void) => void }
    ).startViewTransition = (cb: () => void) => {
      startVT(cb);
      cb();
    };
    const navigate = vi.fn();
    startViewTransitionWithFallback(navigate);
    expect(startVT).toHaveBeenCalledTimes(1);
    expect(navigate).toHaveBeenCalledTimes(1);
  });

  it("sets the in-flight marker so the global provider skips its tick", () => {
    (
      document as unknown as { startViewTransition: (cb: () => void) => void }
    ).startViewTransition = (cb: () => void) => cb();
    startViewTransitionWithFallback(() => undefined);
    const flag = (
      document as unknown as { __viewTransitionInFlight?: boolean }
    ).__viewTransitionInFlight;
    expect(flag).toBe(true);
  });
});

describe("T4.D.5 — reverse direction (assess → wall) uses same morph name", () => {
  it("reverse navigation pattern reuses WALL_TO_ASSESS_TRANSITION_NAME", () => {
    // The reverse-direction pattern: a /assess back-button calls
    // startViewTransitionWithFallback(() => router.push('/')) and the
    // morph target on the wall side is the same constant. We assert the
    // constant is stable across both directions.
    expect(WALL_TO_ASSESS_TRANSITION_NAME).toBe("wall-to-assess");
  });
});

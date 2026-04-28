/**
 * W3 Driver C Spotlight #2 — View Transitions contract.
 *
 * Asserts the contract for the wall->assess morph:
 *   1. Feature detect uses `document.startViewTransition` shape.
 *   2. The shared transition name is the constant (no string drift
 *      between Chapter 10 source and /assess source).
 *   3. The fallback path runs an unconditional navigation when the API
 *      is absent — Firefox users still reach /assess.
 */
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import {
  WALL_TO_ASSESS_TRANSITION_NAME,
  supportsViewTransitions,
  startViewTransitionWithFallback,
} from "../viewTransitions";

describe("viewTransitions — name constant (T3.21 Spotlight #2)", () => {
  it("WALL_TO_ASSESS_TRANSITION_NAME is the canonical 'wall-to-assess' string", () => {
    expect(WALL_TO_ASSESS_TRANSITION_NAME).toBe("wall-to-assess");
  });

  it("name is non-empty and CSS-ident-safe (alpha + dash only)", () => {
    expect(WALL_TO_ASSESS_TRANSITION_NAME).toMatch(/^[a-z][a-z0-9-]*$/);
  });
});

describe("viewTransitions — feature detect", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    delete (globalThis as unknown as Record<string, unknown>).document;
  });

  it("returns true when document.startViewTransition is a function", () => {
    (globalThis as unknown as Record<string, unknown>).document = {
      startViewTransition: () => undefined,
    };
    expect(supportsViewTransitions()).toBe(true);
  });

  it("returns false when document is undefined (SSR)", () => {
    delete (globalThis as unknown as Record<string, unknown>).document;
    expect(supportsViewTransitions()).toBe(false);
  });

  it("returns false when document lacks startViewTransition (Firefox)", () => {
    (globalThis as unknown as Record<string, unknown>).document = {};
    expect(supportsViewTransitions()).toBe(false);
  });
});

describe("viewTransitions — startViewTransitionWithFallback", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    delete (globalThis as unknown as Record<string, unknown>).document;
  });

  it("invokes the navigation callback when API is absent (fallback)", () => {
    delete (globalThis as unknown as Record<string, unknown>).document;
    const navigate = vi.fn();
    startViewTransitionWithFallback(navigate);
    expect(navigate).toHaveBeenCalledOnce();
  });

  it("invokes the navigation callback through startViewTransition when supported", () => {
    const startSpy = vi.fn((cb: () => void) => {
      cb();
      return { finished: Promise.resolve(), ready: Promise.resolve() };
    });
    (globalThis as unknown as Record<string, unknown>).document = {
      startViewTransition: startSpy,
    };
    const navigate = vi.fn();
    startViewTransitionWithFallback(navigate);
    expect(startSpy).toHaveBeenCalledOnce();
    expect(navigate).toHaveBeenCalledOnce();
  });

  it("invokes navigation callback when reducedMotion=true (skips API)", () => {
    const startSpy = vi.fn();
    (globalThis as unknown as Record<string, unknown>).document = {
      startViewTransition: startSpy,
    };
    const navigate = vi.fn();
    startViewTransitionWithFallback(navigate, { reducedMotion: true });
    expect(startSpy).not.toHaveBeenCalled();
    expect(navigate).toHaveBeenCalledOnce();
  });
});

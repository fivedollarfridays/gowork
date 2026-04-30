/**
 * Minimal gsap helper test (Driver B). Driver A's full version supersedes
 * on merge; this exists only to prove the API surface my chapters consume:
 *   - `useGsapScrollTrigger` returns a ref and is SSR/jsdom-safe.
 *   - `useGsapEntrance` is a no-op placeholder under reduced motion.
 *
 * The hook is a no-op in jsdom (no real gsap timeline runs), so the test
 * only checks that the hook can be invoked and does not throw.
 */
import { describe, it, expect, vi, beforeAll } from "vitest";
import { renderHook } from "@testing-library/react";

vi.mock("@/hooks/usePrefersReducedMotion", () => ({
  usePrefersReducedMotion: vi.fn(() => false),
}));

// GSAP ScrollTrigger calls window.matchMedia on register; jsdom does not
// ship it. Stub a minimal MediaQueryList shape so the registration path
// completes under test.
beforeAll(() => {
  if (typeof window !== "undefined" && typeof window.matchMedia !== "function") {
    Object.defineProperty(window, "matchMedia", {
      configurable: true,
      writable: true,
      value: (query: string) => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: () => {},
        removeListener: () => {},
        addEventListener: () => {},
        removeEventListener: () => {},
        dispatchEvent: () => false,
      }),
    });
  }
});

import {
  useGsapScrollTrigger,
  useGsapEntrance,
  registerGsapScrollTrigger,
  __resetGsapRegistrationForTest,
} from "../gsap";

describe("home/gsap helpers", () => {
  it("useGsapScrollTrigger returns a ref object", () => {
    const { result } = renderHook(() =>
      useGsapScrollTrigger(() => undefined),
    );
    expect(result.current).toHaveProperty("current");
  });

  it("useGsapEntrance returns a ref object", () => {
    const { result } = renderHook(() =>
      useGsapEntrance(() => undefined),
    );
    expect(result.current).toHaveProperty("current");
  });
});

describe("registerGsapScrollTrigger (Driver A)", () => {
  it("returns gsap + ScrollTrigger when called", async () => {
    __resetGsapRegistrationForTest();
    const { gsap, ScrollTrigger } = await registerGsapScrollTrigger();
    expect(gsap).toBeDefined();
    expect(ScrollTrigger).toBeDefined();
  });

  it("is idempotent across calls (cached references)", async () => {
    __resetGsapRegistrationForTest();
    const a = await registerGsapScrollTrigger();
    const b = await registerGsapScrollTrigger();
    expect(a.gsap).toBe(b.gsap);
    expect(a.ScrollTrigger).toBe(b.ScrollTrigger);
  });
});

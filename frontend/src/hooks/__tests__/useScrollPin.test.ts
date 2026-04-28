import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { renderHook } from "@testing-library/react";
import { useScrollPin } from "../useScrollPin";

/**
 * T2.10 — useScrollPin.
 *
 * `position: sticky` is unreliable across Safari + iOS Safari + older
 * Firefox at long scroll lengths. Without a JS pinning fallback, chapters
 * "snap" out of pin position mid-scroll on demo day.
 *
 * The hook returns `{ ref, isPinned, computedTop, supportsSticky }`:
 *   - `supportsSticky` reflects `CSS.supports("position: sticky")`
 *   - When the browser supports sticky → `isPinned` follows scroll natively;
 *     hook stays as a ref carrier with no behavior change.
 *   - When NOT supported → the hook returns the computed top via JS so the
 *     consumer can apply `position: fixed` instead.
 *
 * SSR-safe: defaults to `supportsSticky: true` on the server (the common
 * case) so initial markup doesn't flash a JS-fixed layout.
 */

describe("T2.10 — useScrollPin (CSS.supports sticky branch)", () => {
  let originalSupports: typeof CSS.supports | undefined;

  beforeEach(() => {
    // Spy on CSS.supports so each test can flip the branch.
    if (typeof window !== "undefined" && typeof window.CSS !== "undefined") {
      originalSupports = window.CSS.supports;
    }
  });

  afterEach(() => {
    if (originalSupports && typeof window !== "undefined") {
      window.CSS.supports = originalSupports;
    }
    vi.restoreAllMocks();
  });

  it("returns supportsSticky=true when CSS.supports('position: sticky') is true", () => {
    if (typeof window !== "undefined") {
      window.CSS.supports = vi.fn().mockReturnValue(true) as unknown as typeof CSS.supports;
    }
    const { result } = renderHook(() => useScrollPin());
    expect(result.current.supportsSticky).toBe(true);
  });

  it("returns supportsSticky=false when CSS.supports returns false", () => {
    if (typeof window !== "undefined") {
      window.CSS.supports = vi.fn().mockReturnValue(false) as unknown as typeof CSS.supports;
    }
    const { result } = renderHook(() => useScrollPin());
    expect(result.current.supportsSticky).toBe(false);
  });

  it("exposes a ref attachable to a DOM element", () => {
    const { result } = renderHook(() => useScrollPin());
    expect(result.current.ref).toBeDefined();
    expect("current" in result.current.ref).toBe(true);
  });

  it("isPinned is a boolean", () => {
    const { result } = renderHook(() => useScrollPin());
    expect(typeof result.current.isPinned).toBe("boolean");
  });

  it("computedTop is a number (or 0 default)", () => {
    const { result } = renderHook(() => useScrollPin());
    expect(typeof result.current.computedTop).toBe("number");
  });
});

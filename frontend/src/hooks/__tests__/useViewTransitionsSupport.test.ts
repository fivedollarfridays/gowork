import { describe, it, expect, afterEach } from "vitest";
import { renderHook } from "@testing-library/react";
import { useViewTransitionsSupport } from "../useViewTransitionsSupport";

describe("useViewTransitionsSupport (T1.32)", () => {
  const original = (document as unknown as { startViewTransition?: unknown })
    .startViewTransition;

  afterEach(() => {
    if (original === undefined) {
      delete (document as unknown as { startViewTransition?: unknown })
        .startViewTransition;
    } else {
      (document as unknown as { startViewTransition?: unknown }).startViewTransition =
        original;
    }
  });

  it("returns false when document.startViewTransition is undefined", () => {
    delete (document as unknown as { startViewTransition?: unknown }).startViewTransition;
    const { result } = renderHook(() => useViewTransitionsSupport());
    expect(result.current).toBe(false);
  });

  it("returns true when document.startViewTransition is a function", () => {
    (document as unknown as { startViewTransition?: unknown }).startViewTransition =
      () => undefined;
    const { result } = renderHook(() => useViewTransitionsSupport());
    expect(result.current).toBe(true);
  });

  it("does not re-render the boolean across rerenders (memoized)", () => {
    (document as unknown as { startViewTransition?: unknown }).startViewTransition =
      () => undefined;
    const { result, rerender } = renderHook(() => useViewTransitionsSupport());
    const first = result.current;
    rerender();
    expect(result.current).toBe(first);
  });
});

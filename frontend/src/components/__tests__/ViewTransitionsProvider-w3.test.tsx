/**
 * W3 Driver C — T3.21 — additive ViewTransitionsProvider extension.
 *
 * Asserts that when a transition is ALREADY in flight (the chapter-10
 * CTA called `document.startViewTransition` immediately before the
 * route change), the provider's pathname-watcher does NOT queue a
 * redundant second transition. Without this, the cinematic morph gets
 * interrupted by the empty page-level transition.
 *
 * The implementation hint: ViewTransitionsProvider checks
 * `document.__viewTransitionInFlight === true` (a one-shot marker set
 * by `startViewTransitionWithFallback`) and skips its own call when
 * true, then clears the marker.
 */
import { render } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

let mockPathname = "/";
let mockReducedMotion = false;
vi.mock("next/navigation", () => ({
  usePathname: () => mockPathname,
}));
vi.mock("framer-motion", () => ({
  useReducedMotion: () => mockReducedMotion,
}));

import { ViewTransitionsProvider } from "../ViewTransitionsProvider";

const docAny = () =>
  document as unknown as {
    startViewTransition?: (cb: () => void) => unknown;
    __viewTransitionInFlight?: boolean;
  };

describe("ViewTransitionsProvider — W3 in-flight guard (additive)", () => {
  beforeEach(() => {
    mockPathname = "/";
    mockReducedMotion = false;
    delete docAny().startViewTransition;
    delete docAny().__viewTransitionInFlight;
  });

  it("skips redundant startViewTransition when __viewTransitionInFlight is true", () => {
    const spy = vi.fn();
    Object.defineProperty(document, "startViewTransition", {
      value: spy,
      writable: true,
      configurable: true,
    });

    const { rerender } = render(
      <ViewTransitionsProvider>
        <p>before</p>
      </ViewTransitionsProvider>,
    );

    // Caller marks transition in-flight, then triggers a route change.
    docAny().__viewTransitionInFlight = true;
    mockPathname = "/assess";
    rerender(
      <ViewTransitionsProvider>
        <p>after</p>
      </ViewTransitionsProvider>,
    );

    expect(spy).not.toHaveBeenCalled();
    // Marker is cleared so subsequent navigations get the normal
    // page-level transition.
    expect(docAny().__viewTransitionInFlight).toBe(false);

    delete docAny().startViewTransition;
  });

  it("still fires page-level transition when no in-flight marker", () => {
    const spy = vi.fn();
    Object.defineProperty(document, "startViewTransition", {
      value: spy,
      writable: true,
      configurable: true,
    });

    const { rerender } = render(
      <ViewTransitionsProvider>
        <p>before</p>
      </ViewTransitionsProvider>,
    );
    mockPathname = "/jobs";
    rerender(
      <ViewTransitionsProvider>
        <p>after</p>
      </ViewTransitionsProvider>,
    );
    expect(spy).toHaveBeenCalledTimes(1);
    delete docAny().startViewTransition;
  });
});

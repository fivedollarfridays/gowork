/**
 * polish-2 T48 — Ch01 cursor particle trail tests.
 *
 * - 12-particle amber trail with 600ms decay.
 * - Disabled on coarse pointer + reduced motion.
 * - Constrained to `.ch01` — pointermove outside Ch1 does not add particles.
 */
import React from "react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { render, cleanup } from "@testing-library/react";

vi.mock("@/hooks/usePrefersReducedMotion", () => ({
  usePrefersReducedMotion: vi.fn(() => false),
}));

import { usePrefersReducedMotion } from "@/hooks/usePrefersReducedMotion";
import { Ch01CursorTrail } from "../Ch01CursorTrail";

const reducedMotionMock = vi.mocked(usePrefersReducedMotion);

afterEach(() => {
  cleanup();
  reducedMotionMock.mockReturnValue(false);
  Object.defineProperty(navigator, "maxTouchPoints", {
    value: 0,
    configurable: true,
  });
  // Restore matchMedia default
  Object.defineProperty(window, "matchMedia", {
    value: (q: string) => ({
      matches: false,
      media: q,
      addEventListener: () => undefined,
      removeEventListener: () => undefined,
      addListener: () => undefined,
      removeListener: () => undefined,
      onchange: null,
      dispatchEvent: () => false,
    }),
    configurable: true,
    writable: true,
  });
});

describe("Ch01CursorTrail (polish-2 T48)", () => {
  it("returns null on coarse-pointer (touch) devices", () => {
    Object.defineProperty(navigator, "maxTouchPoints", {
      value: 5,
      configurable: true,
    });
    Object.defineProperty(window, "matchMedia", {
      value: (q: string) => ({
        matches: q.includes("coarse"),
        media: q,
        addEventListener: () => undefined,
        removeEventListener: () => undefined,
        addListener: () => undefined,
        removeListener: () => undefined,
        onchange: null,
        dispatchEvent: () => false,
      }),
      configurable: true,
      writable: true,
    });
    const { container } = render(<Ch01CursorTrail />);
    expect(container.querySelector("[data-ch01-trail-root]")).toBeNull();
  });

  it("returns null when reduced-motion is on", () => {
    reducedMotionMock.mockReturnValue(true);
    const { container } = render(<Ch01CursorTrail />);
    expect(container.querySelector("[data-ch01-trail-root]")).toBeNull();
  });

  it("renders a fixed-position root element on desktop", () => {
    const { container } = render(<Ch01CursorTrail />);
    const root = container.querySelector("[data-ch01-trail-root]");
    expect(root).not.toBeNull();
  });

  it("adds a [data-trail] particle node when pointermove fires inside .ch01", () => {
    document.body.innerHTML =
      '<section class="ch01" data-testid="ch01-section" style="position:absolute;top:0;left:0;width:1000px;height:1000px"></section>';
    const ch1 = document.querySelector(".ch01") as HTMLElement;
    const { container } = render(<Ch01CursorTrail />);
    // Dispatch a pointermove on the chapter section
    ch1.dispatchEvent(
      new PointerEvent("pointermove", {
        clientX: 200,
        clientY: 200,
        bubbles: true,
      }),
    );
    const particles = container.querySelectorAll("[data-trail]");
    expect(particles.length).toBeGreaterThanOrEqual(1);
  });

  it("does not add particles when pointermove fires outside .ch01", () => {
    document.body.innerHTML =
      '<section class="ch01" style="position:absolute;top:0;left:0;width:1000px;height:1000px"></section><section class="ch02" style="position:absolute;top:1000px;left:0;width:1000px;height:1000px"></section>';
    const { container } = render(<Ch01CursorTrail />);
    // Fire pointermove with no Ch1 ancestor — directly on document
    document.dispatchEvent(
      new PointerEvent("pointermove", {
        clientX: 200,
        clientY: 1500,
      }),
    );
    const particles = container.querySelectorAll("[data-trail]");
    expect(particles.length).toBe(0);
  });

  it("caps the active particle pool to 12", () => {
    document.body.innerHTML =
      '<section class="ch01" style="position:absolute;top:0;left:0;width:1000px;height:1000px"></section>';
    const ch1 = document.querySelector(".ch01") as HTMLElement;
    const { container } = render(<Ch01CursorTrail />);
    for (let i = 0; i < 30; i += 1) {
      ch1.dispatchEvent(
        new PointerEvent("pointermove", {
          clientX: 100 + i,
          clientY: 200,
          bubbles: true,
        }),
      );
    }
    const particles = container.querySelectorAll("[data-trail]");
    expect(particles.length).toBeLessThanOrEqual(12);
  });
});

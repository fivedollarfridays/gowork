/**
 * T4.D.6 — Scroll-velocity reactive motion-blur (Wave 4 polish).
 *
 * Subtle motion-blur on the Mapbox background when scroll velocity
 * exceeds the threshold. Threshold-based — not always-on. Disabled
 * with reduced-motion.
 *
 * The component renders nothing visible itself; it applies a CSS
 * `filter: blur(...)` on the wrapper element it owns. The Mapbox
 * canvas mounts inside that wrapper.
 *
 * Contract:
 *   - velocity below threshold → filter: 'none'
 *   - velocity above threshold → filter: 'blur(2px)'
 *   - reduced-motion → filter: 'none' regardless of velocity
 */

import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render } from "@testing-library/react";

const reducedMotionMock = vi.fn();
const scrollVelocityMock = vi.fn();

vi.mock("@/hooks/usePrefersReducedMotion", () => ({
  usePrefersReducedMotion: () => reducedMotionMock(),
}));

vi.mock("@/hooks/useScrollVelocity", () => ({
  useScrollVelocity: () => scrollVelocityMock(),
}));

beforeEach(() => {
  reducedMotionMock.mockReset();
  scrollVelocityMock.mockReset();
  reducedMotionMock.mockReturnValue(false);
  scrollVelocityMock.mockReturnValue({ velocity: 0, isFast: false });
});

describe("T4.D.6 — MapMotionBlur applies blur on fast scroll", () => {
  it("renders an attached wrapper with no blur when velocity is low", async () => {
    scrollVelocityMock.mockReturnValue({ velocity: 0.5, isFast: false });
    const { MapMotionBlur } = await import("../MapMotionBlur");
    const { getByTestId } = render(
      <MapMotionBlur>
        <div data-testid="child">child</div>
      </MapMotionBlur>,
    );
    const wrapper = getByTestId("map-motion-blur");
    expect(wrapper.style.filter === "" || wrapper.style.filter === "none").toBe(
      true,
    );
  });

  it("applies filter: blur(2px) when velocity is fast", async () => {
    scrollVelocityMock.mockReturnValue({ velocity: 5, isFast: true });
    const { MapMotionBlur } = await import("../MapMotionBlur");
    const { getByTestId } = render(
      <MapMotionBlur>
        <div data-testid="child">child</div>
      </MapMotionBlur>,
    );
    const wrapper = getByTestId("map-motion-blur");
    expect(wrapper.style.filter).toContain("blur");
  });

  it("never applies blur when reduced-motion is on (even at high velocity)", async () => {
    reducedMotionMock.mockReturnValue(true);
    scrollVelocityMock.mockReturnValue({ velocity: 10, isFast: true });
    const { MapMotionBlur } = await import("../MapMotionBlur");
    const { getByTestId } = render(
      <MapMotionBlur>
        <div data-testid="child">child</div>
      </MapMotionBlur>,
    );
    const wrapper = getByTestId("map-motion-blur");
    expect(wrapper.style.filter === "" || wrapper.style.filter === "none").toBe(
      true,
    );
  });

  it("applies a transition on the filter property for smoothness", async () => {
    const { MapMotionBlur } = await import("../MapMotionBlur");
    const { getByTestId } = render(
      <MapMotionBlur>
        <div data-testid="child">child</div>
      </MapMotionBlur>,
    );
    const wrapper = getByTestId("map-motion-blur");
    expect(wrapper.style.transition).toMatch(/filter/);
  });

  it("renders children inside the wrapper", async () => {
    const { MapMotionBlur } = await import("../MapMotionBlur");
    const { getByTestId } = render(
      <MapMotionBlur>
        <div data-testid="child">child</div>
      </MapMotionBlur>,
    );
    expect(getByTestId("child")).toBeInTheDocument();
  });

  it("data-fallback='reduced' set when reduced motion is active", async () => {
    reducedMotionMock.mockReturnValue(true);
    const { MapMotionBlur } = await import("../MapMotionBlur");
    const { getByTestId } = render(
      <MapMotionBlur>
        <div data-testid="child">child</div>
      </MapMotionBlur>,
    );
    const wrapper = getByTestId("map-motion-blur");
    expect(wrapper.getAttribute("data-fallback")).toBe("reduced");
  });

  it("data-fallback='live' set when active life-layer is on", async () => {
    scrollVelocityMock.mockReturnValue({ velocity: 5, isFast: true });
    const { MapMotionBlur } = await import("../MapMotionBlur");
    const { getByTestId } = render(
      <MapMotionBlur>
        <div data-testid="child">child</div>
      </MapMotionBlur>,
    );
    const wrapper = getByTestId("map-motion-blur");
    expect(wrapper.getAttribute("data-fallback")).toBe("live");
  });
});

import { describe, it, expect, vi, afterEach, beforeEach } from "vitest";
import { render, fireEvent, act } from "@testing-library/react";
import { MapCursorFlashlight } from "../MapCursorFlashlight";

vi.mock("../../../hooks/usePrefersReducedMotion", () => ({
  usePrefersReducedMotion: vi.fn(() => false),
}));

import { usePrefersReducedMotion } from "../../../hooks/usePrefersReducedMotion";

beforeEach(() => {
  Object.defineProperty(navigator, "maxTouchPoints", { value: 0, configurable: true });
  vi.mocked(usePrefersReducedMotion).mockReturnValue(false);
  // Stub rAF so handlers fire synchronously inside act().
  vi.spyOn(window, "requestAnimationFrame").mockImplementation(
    (cb: FrameRequestCallback) => {
      cb(0);
      return 1;
    },
  );
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("MapCursorFlashlight (T4.A.3)", () => {
  it("renders a flashlight overlay div over the map", () => {
    const { container } = render(<MapCursorFlashlight />);
    const overlay = container.querySelector('[data-testid="map-cursor-flashlight"]');
    expect(overlay).not.toBeNull();
  });

  it("updates --cursor-x and --cursor-y on pointermove (rAF-throttled)", () => {
    const { container } = render(<MapCursorFlashlight />);
    const overlay = container.querySelector(
      '[data-testid="map-cursor-flashlight"]',
    ) as HTMLElement;
    expect(overlay).not.toBeNull();
    act(() => {
      fireEvent.pointerMove(window, { clientX: 600, clientY: 400 });
    });
    const x = overlay.style.getPropertyValue("--cursor-x");
    const y = overlay.style.getPropertyValue("--cursor-y");
    expect(x).toBeTruthy();
    expect(y).toBeTruthy();
  });

  it("renders a radial-gradient mask at the configured radius", () => {
    const { container } = render(<MapCursorFlashlight radiusPx={200} />);
    const overlay = container.querySelector(
      '[data-testid="map-cursor-flashlight"]',
    ) as HTMLElement;
    const maskImage = overlay.style.getPropertyValue("mask-image");
    const webkitMaskImage = overlay.style.getPropertyValue("-webkit-mask-image");
    // jsdom may store under either prop; either non-empty string passes.
    const value = maskImage || webkitMaskImage;
    expect(value).toMatch(/radial-gradient/);
    expect(value).toMatch(/200px/);
  });

  it("disables the mask under reduced-motion (full opacity, no flashlight)", () => {
    vi.mocked(usePrefersReducedMotion).mockReturnValue(true);
    const { container } = render(<MapCursorFlashlight />);
    const overlay = container.querySelector(
      '[data-testid="map-cursor-flashlight"]',
    ) as HTMLElement;
    expect(overlay.dataset.fallback).toBe("disabled");
  });

  it("disables the mask on touch devices (no pointer hover)", () => {
    Object.defineProperty(navigator, "maxTouchPoints", { value: 5, configurable: true });
    const { container } = render(<MapCursorFlashlight />);
    const overlay = container.querySelector(
      '[data-testid="map-cursor-flashlight"]',
    ) as HTMLElement;
    expect(overlay.dataset.fallback).toBe("disabled");
  });

  it("is aria-hidden (decorative; not announced to screen readers)", () => {
    const { container } = render(<MapCursorFlashlight />);
    const overlay = container.querySelector(
      '[data-testid="map-cursor-flashlight"]',
    ) as HTMLElement;
    expect(overlay.getAttribute("aria-hidden")).toBe("true");
  });

  it("uses pointer-events:none so map interactions pass through", () => {
    const { container } = render(<MapCursorFlashlight />);
    const overlay = container.querySelector(
      '[data-testid="map-cursor-flashlight"]',
    ) as HTMLElement;
    expect(overlay.style.pointerEvents).toBe("none");
  });
});

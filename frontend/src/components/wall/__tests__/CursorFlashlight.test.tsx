import { describe, it, expect, vi, afterEach } from "vitest";
import { render } from "@testing-library/react";
import { CursorFlashlight } from "../CursorFlashlight";

vi.mock("../../../hooks/useCursorPosition", () => ({
  useCursorPosition: vi.fn(() => ({ x: 0.3, y: 0.7, vx: 0, vy: 0 })),
}));

vi.mock("../../../hooks/usePrefersReducedMotion", () => ({
  usePrefersReducedMotion: vi.fn(() => false),
}));

import { usePrefersReducedMotion } from "../../../hooks/usePrefersReducedMotion";

afterEach(() => {
  vi.mocked(usePrefersReducedMotion).mockReturnValue(false);
  Object.defineProperty(navigator, "maxTouchPoints", { value: 0, configurable: true });
});

describe("CursorFlashlight (T1.61)", () => {
  it("renders a flashlight overlay div", () => {
    const { container } = render(<CursorFlashlight />);
    const overlay = container.querySelector('[data-testid="cursor-flashlight"]');
    expect(overlay).not.toBeNull();
  });

  it("sets --flashlight-x and --flashlight-y CSS variables to cursor position", () => {
    const { container } = render(<CursorFlashlight />);
    const overlay = container.querySelector(
      '[data-testid="cursor-flashlight"]',
    ) as HTMLElement | null;
    expect(overlay).not.toBeNull();
    expect(overlay?.style.getPropertyValue("--flashlight-x")).toContain("30");
    expect(overlay?.style.getPropertyValue("--flashlight-y")).toContain("70");
  });

  it("applies a uniform-bright style when reduced-motion is on", () => {
    vi.mocked(usePrefersReducedMotion).mockReturnValue(true);
    const { container } = render(<CursorFlashlight />);
    const overlay = container.querySelector(
      '[data-testid="cursor-flashlight"]',
    ) as HTMLElement | null;
    expect(overlay).not.toBeNull();
    expect(overlay?.dataset.fallback).toBe("uniform");
  });

  it("applies uniform fallback on touch devices", () => {
    Object.defineProperty(navigator, "maxTouchPoints", { value: 5, configurable: true });
    const { container } = render(<CursorFlashlight />);
    const overlay = container.querySelector(
      '[data-testid="cursor-flashlight"]',
    ) as HTMLElement | null;
    expect(overlay?.dataset.fallback).toBe("uniform");
  });
});

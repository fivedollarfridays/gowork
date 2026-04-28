import { describe, it, expect, vi, afterEach } from "vitest";
import { render } from "@testing-library/react";
import { CursorTrail } from "../CursorTrail";

vi.mock("../../../hooks/useCursorPosition", () => ({
  useCursorPosition: vi.fn(() => ({ x: 0.4, y: 0.3, vx: 0, vy: 0 })),
}));

vi.mock("../../../hooks/usePrefersReducedMotion", () => ({
  usePrefersReducedMotion: vi.fn(() => false),
}));

import { usePrefersReducedMotion } from "../../../hooks/usePrefersReducedMotion";

afterEach(() => {
  vi.mocked(usePrefersReducedMotion).mockReturnValue(false);
  Object.defineProperty(navigator, "maxTouchPoints", { value: 0, configurable: true });
});

describe("CursorTrail (T1.60)", () => {
  it("renders a fixed dot element on desktop", () => {
    const { container } = render(<CursorTrail />);
    const dot = container.querySelector('[data-testid="cursor-trail-dot"]');
    expect(dot).not.toBeNull();
  });

  it("returns null on touch devices", () => {
    Object.defineProperty(navigator, "maxTouchPoints", { value: 5, configurable: true });
    const { container } = render(<CursorTrail />);
    expect(container.querySelector('[data-testid="cursor-trail-dot"]')).toBeNull();
  });

  it("returns null when reduced-motion is on (T1.62 fallback)", () => {
    vi.mocked(usePrefersReducedMotion).mockReturnValue(true);
    const { container } = render(<CursorTrail />);
    expect(container.querySelector('[data-testid="cursor-trail-dot"]')).toBeNull();
  });

  it("dot uses pointer-events: none and position: fixed (no layout shift)", () => {
    const { container } = render(<CursorTrail />);
    const dot = container.querySelector(
      '[data-testid="cursor-trail-dot"]',
    ) as HTMLElement | null;
    expect(dot).not.toBeNull();
    expect(dot?.style.position).toBe("fixed");
    expect(dot?.style.pointerEvents).toBe("none");
  });
});

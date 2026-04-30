/**
 * HeaderProgressRail — polish-2 T10.
 *
 * 8-segment cyan-fill bar pinned just below the SiteHeader. As scroll
 * passes each chapter boundary, that segment fills cyan; the active
 * segment glows. Reduced-motion: collapse to a single thin bar.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render } from "@testing-library/react";

vi.mock("@/hooks/useScrollProgress", () => ({
  useScrollProgress: vi.fn(),
}));
vi.mock("@/hooks/usePrefersReducedMotion", () => ({
  usePrefersReducedMotion: vi.fn(),
}));

import { useScrollProgress } from "@/hooks/useScrollProgress";
import { usePrefersReducedMotion } from "@/hooks/usePrefersReducedMotion";
import { HeaderProgressRail } from "../HeaderProgressRail";

function setProgress(total: number, chapterIdx: number, inChapter: number): void {
  vi.mocked(useScrollProgress).mockReturnValue({
    chapter: chapterIdx,
    progressInChapter: inChapter,
    totalProgress: total,
  });
}

describe("HeaderProgressRail — segment states (T10)", () => {
  beforeEach(() => {
    vi.mocked(usePrefersReducedMotion).mockReturnValue(false);
    setProgress(0, 0, 0);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("renders 8 segments", () => {
    const { container } = render(<HeaderProgressRail />);
    const segments = container.querySelectorAll("[data-progress-segment]");
    expect(segments).toHaveLength(8);
  });

  it("at scroll 0%, segment 1 is the 'now' state and others are 'pending'", () => {
    setProgress(0, 0, 0);
    const { container } = render(<HeaderProgressRail />);
    const segments = container.querySelectorAll("[data-progress-segment]");
    expect(segments[0].getAttribute("data-state")).toBe("now");
    expect(segments[1].getAttribute("data-state")).toBe("pending");
    expect(segments[7].getAttribute("data-state")).toBe("pending");
  });

  it("at scroll into chapter 3 (≥25%), segs 1+2 are done, seg 3 is now", () => {
    // chapter index is 0-based on useScrollProgress. chapter 3 = idx 2.
    setProgress(0.25, 2, 0.0);
    const { container } = render(<HeaderProgressRail />);
    const segments = container.querySelectorAll("[data-progress-segment]");
    expect(segments[0].getAttribute("data-state")).toBe("done");
    expect(segments[1].getAttribute("data-state")).toBe("done");
    expect(segments[2].getAttribute("data-state")).toBe("now");
    expect(segments[3].getAttribute("data-state")).toBe("pending");
  });

  it("at the last chapter, all earlier segments are done and seg 8 is now", () => {
    setProgress(0.9, 7, 0.5);
    const { container } = render(<HeaderProgressRail />);
    const segments = container.querySelectorAll("[data-progress-segment]");
    for (let i = 0; i < 7; i++) {
      expect(segments[i].getAttribute("data-state")).toBe("done");
    }
    expect(segments[7].getAttribute("data-state")).toBe("now");
  });

  it("collapses to a single bar when prefers-reduced-motion is on", () => {
    vi.mocked(usePrefersReducedMotion).mockReturnValue(true);
    setProgress(0.5, 4, 0);
    const { container } = render(<HeaderProgressRail />);
    expect(container.querySelector(".header-progress-rail--reduced")).toBeTruthy();
    expect(container.querySelectorAll("[data-progress-segment]").length).toBe(0);
    const bar = container.querySelector(".header-progress-rail__bar") as HTMLElement;
    expect(bar).toBeTruthy();
    // 50% scroll → bar width 50%
    expect(bar.style.width).toBe("50%");
  });
});

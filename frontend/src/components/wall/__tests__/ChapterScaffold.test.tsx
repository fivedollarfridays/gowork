import React from "react";
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { render, cleanup } from "@testing-library/react";

/**
 * T2.6 — ChapterScaffold.
 *
 * Reusable wrapper every chapter (1–10) renders inside. Provides:
 *   - sticky positioning (chapter pins while camera flies underneath)
 *   - scroll-tied opacity (overlay fades 0–20%, holds 20–80%, fades 80–100%)
 *   - aria-live region for chapter title (screen-reader parity)
 *   - reduced-motion path: full opacity + no fade
 *
 * Tests verify the contract Drivers B/C consume — they pass `chapterNumber`,
 * `chapterId`, `chapterProgress`, `children`. The scaffold orchestrates the
 * shared concerns so chapter components stay focused on their editorial.
 */

const reducedMotionMock = vi.fn();

vi.mock("@/hooks/usePrefersReducedMotion", () => ({
  usePrefersReducedMotion: () => reducedMotionMock(),
}));

beforeEach(() => {
  reducedMotionMock.mockReset();
  reducedMotionMock.mockReturnValue(false);
});

afterEach(() => {
  cleanup();
});

describe("T2.6 — ChapterScaffold renders children + chapter title slot", () => {
  it("renders the children slot (chapter overlay content)", async () => {
    const { default: ChapterScaffold } = await import("../ChapterScaffold");
    const { getByText } = render(
      React.createElement(
        ChapterScaffold,
        { chapterNumber: 1, chapterId: "continental", chapterProgress: 0.5 },
        React.createElement("p", null, "Carlos lives here."),
      ),
    );
    expect(getByText("Carlos lives here.")).toBeInTheDocument();
  });

  it("renders an aria-live region announcing the chapter id", async () => {
    const { default: ChapterScaffold } = await import("../ChapterScaffold");
    const { container } = render(
      React.createElement(
        ChapterScaffold,
        { chapterNumber: 3, chapterId: "neighborhood", chapterProgress: 0.3 },
        React.createElement("p", null, "..."),
      ),
    );
    const live = container.querySelector('[aria-live]');
    expect(live).not.toBeNull();
    expect(live?.getAttribute("aria-live")).toBe("polite");
  });
});

describe("T2.6 — opacity follows chapter progress curve (fade in 0-20, hold 20-80, fade 80-100)", () => {
  it("opacity 0 at progress=0", async () => {
    const { computeOverlayOpacity } = await import("../ChapterScaffold");
    expect(computeOverlayOpacity(0, false)).toBeCloseTo(0, 3);
  });

  it("opacity ~1 in the hold zone (progress=0.5)", async () => {
    const { computeOverlayOpacity } = await import("../ChapterScaffold");
    expect(computeOverlayOpacity(0.5, false)).toBeCloseTo(1, 3);
  });

  it("opacity ramps in by progress=0.2 (end of fade-in)", async () => {
    const { computeOverlayOpacity } = await import("../ChapterScaffold");
    expect(computeOverlayOpacity(0.2, false)).toBeCloseTo(1, 3);
  });

  it("opacity 0 at progress=1 (post fade-out)", async () => {
    const { computeOverlayOpacity } = await import("../ChapterScaffold");
    expect(computeOverlayOpacity(1, false)).toBeCloseTo(0, 3);
  });

  it("opacity intermediate at progress=0.1 (mid fade-in)", async () => {
    const { computeOverlayOpacity } = await import("../ChapterScaffold");
    const value = computeOverlayOpacity(0.1, false);
    expect(value).toBeGreaterThan(0);
    expect(value).toBeLessThan(1);
  });
});

describe("T2.6 — reduced-motion path collapses to instant cuts", () => {
  it("opacity is constant 1 (no fade) when reduced-motion=true", async () => {
    const { computeOverlayOpacity } = await import("../ChapterScaffold");
    expect(computeOverlayOpacity(0, true)).toBe(1);
    expect(computeOverlayOpacity(0.5, true)).toBe(1);
    expect(computeOverlayOpacity(1, true)).toBe(1);
  });

  it("rendered scaffold uses opacity 1 across all progress with reduced-motion", async () => {
    reducedMotionMock.mockReturnValue(true);
    const { default: ChapterScaffold } = await import("../ChapterScaffold");
    const { container } = render(
      React.createElement(
        ChapterScaffold,
        { chapterNumber: 2, chapterId: "city", chapterProgress: 0 },
        React.createElement("p", null, "..."),
      ),
    );
    const overlay = container.querySelector('[data-chapter-overlay="true"]') as HTMLElement;
    expect(overlay).not.toBeNull();
    // Inline style or style-set computed — read style.opacity.
    expect(overlay.style.opacity).toBe("1");
  });
});

describe("T2.6 — chapter id propagates to data attributes (consumer hook)", () => {
  it("data-chapter-id matches the prop", async () => {
    const { default: ChapterScaffold } = await import("../ChapterScaffold");
    const { container } = render(
      React.createElement(
        ChapterScaffold,
        { chapterNumber: 5, chapterId: "labyrinth", chapterProgress: 0.5 },
        null,
      ),
    );
    const root = container.querySelector('[data-chapter-id]') as HTMLElement;
    expect(root.getAttribute("data-chapter-id")).toBe("labyrinth");
    expect(root.getAttribute("data-chapter-number")).toBe("5");
  });
});

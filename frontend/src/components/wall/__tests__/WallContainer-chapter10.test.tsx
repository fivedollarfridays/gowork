/**
 * W3 Driver C — T3.23 — WallContainer renders Chapter 10 in slot 10.
 *
 * Asserts that WallContainer's ChaptersSequence appends Chapter10
 * AFTER chapters 1-5 (and the W3 placeholders for 6-9 once Drivers
 * A+B land them; here we just check Ch10 exists). The Ch10 section
 * must come last in DOM order.
 */
import React from "react";
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { render, cleanup } from "@testing-library/react";

vi.mock("../MapboxScene", () => ({
  default: () => React.createElement("div", { "data-testid": "mapbox-scene-stub" }),
}));

vi.mock("@/hooks/useTranslation", () => ({
  useTranslation: () => ({
    t: (key: string) => key,
    locale: "en",
    setLocale: () => undefined,
  }),
  TranslationProvider: ({ children }: { children: React.ReactNode }) =>
    React.createElement(React.Fragment, null, children),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn(), back: vi.fn() }),
}));

vi.mock("@/hooks/useDeviceCapability", () => ({
  useDeviceCapability: () => ({
    tier: "high",
    supportsWebGL: true,
    isMobile: false,
    deviceMemoryGb: 16,
    hardwareConcurrency: 12,
    prefersReducedData: false,
  }),
}));

// W3 Driver D — differentiate dynamic loaders so MapboxScene + cliff
// chart fallbacks don't collide on the same testid.
vi.mock("next/dynamic", () => ({
  default: (loader: () => Promise<{ default: React.ComponentType }>) => {
    let Component: React.ComponentType | null = null;
    void loader().then((mod) => {
      Component = mod.default;
    });
    const loaderSrc = String(loader);
    const isCliffChart = /BenefitsCliffChart/.test(loaderSrc);
    const fallbackTestId = isCliffChart
      ? "cliff-chart-dynamic-stub"
      : "mapbox-scene-stub";
    const Wrapper: React.FC<Record<string, unknown>> = (props) => {
      if (Component) return React.createElement(Component, props);
      return React.createElement("div", { "data-testid": fallbackTestId });
    };
    return Wrapper;
  },
}));

let chapterMock = { currentChapter: 1, chapterProgress: 0, totalProgress: 0 };

vi.mock("@/hooks/useChapterProgress", () => ({
  useChapterProgress: () => ({
    currentChapter: chapterMock.currentChapter,
    chapterProgress: chapterMock.chapterProgress,
    nextChapter: Math.min(10, chapterMock.currentChapter + 1),
    isTransitioning: false,
  }),
}));

vi.mock("@/hooks/useScrollProgress", () => ({
  useScrollProgress: () => ({
    chapter: Math.max(0, chapterMock.currentChapter - 1),
    progressInChapter: chapterMock.chapterProgress,
    totalProgress: chapterMock.totalProgress,
  }),
}));

beforeEach(() => {
  process.env.NEXT_PUBLIC_MAPBOX_TOKEN = "pk.eyJ1IjoiZ293b3JrIn0.sig";
  chapterMock = { currentChapter: 10, chapterProgress: 0.5, totalProgress: 0.95 };
});

afterEach(() => {
  cleanup();
  delete process.env.NEXT_PUBLIC_MAPBOX_TOKEN;
});

describe("W3 Driver C — WallContainer renders Chapter 10 (T3.23)", () => {
  it("renders Chapter 10 (find-your-path) section", async () => {
    const { default: WallContainer } = await import("../WallContainer");
    const { container } = render(React.createElement(WallContainer));
    expect(
      container.querySelector('[data-chapter="10"]'),
    ).toBeInTheDocument();
  });

  it("Chapter 10 is the LAST chapter section in DOM order", async () => {
    const { default: WallContainer } = await import("../WallContainer");
    const { container } = render(React.createElement(WallContainer));
    const sections = container.querySelectorAll("[data-chapter-id], [data-chapter]");
    const markers: string[] = [];
    sections.forEach((el) => {
      const id =
        el.getAttribute("data-chapter-id") ?? el.getAttribute("data-chapter");
      if (id) markers.push(id);
    });
    expect(markers.length).toBeGreaterThan(0);
    expect(markers[markers.length - 1]).toBe("10");
  });

  it("Chapter 10 renders the primary CTA button", async () => {
    const { default: WallContainer } = await import("../WallContainer");
    const { container } = render(React.createElement(WallContainer));
    expect(
      container.querySelector('[data-testid="chapter10-cta-primary"]'),
    ).toBeInTheDocument();
  });
});

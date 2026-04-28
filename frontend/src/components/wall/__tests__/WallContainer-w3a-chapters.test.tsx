/**
 * W3 Driver A — WallContainer extension test (T3.6).
 *
 * Confirms that WallContainer composes Chapter06TheMath and
 * Chapter09AnyCity in the right slots, and that Drivers B/C will be able
 * to add 7/8/10 without breaking these assertions. Tests are slot-aware
 * but tolerant of TODO placeholders for Drivers B/C/D-coordination.
 */
import React from "react";
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { render, cleanup } from "@testing-library/react";

vi.mock("../MapboxScene", () => ({
  default: () =>
    React.createElement("div", { "data-testid": "mapbox-scene-stub" }),
}));

// Driver C's Chapter10 calls useRouter; once all W3 chapters merge, this
// test renders the full spine and must mock next/navigation too.
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn(), back: vi.fn() }),
  useSearchParams: () => new URLSearchParams(),
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
  chapterMock = { currentChapter: 1, chapterProgress: 0, totalProgress: 0 };
});

afterEach(() => {
  cleanup();
  delete process.env.NEXT_PUBLIC_MAPBOX_TOKEN;
});

describe("W3 Driver A — WallContainer renders Ch6 + Ch9", () => {
  it("renders Chapter 6 (the math) section", async () => {
    const { default: WallContainer } = await import("../WallContainer");
    const { container } = render(React.createElement(WallContainer));
    expect(
      container.querySelector('[data-chapter="06"]'),
    ).toBeInTheDocument();
  });

  it("renders Chapter 9 (any city) section", async () => {
    const { default: WallContainer } = await import("../WallContainer");
    const { container } = render(React.createElement(WallContainer));
    expect(
      container.querySelector('[data-chapter="09"]'),
    ).toBeInTheDocument();
  });

  it("Ch6 renders AFTER Ch5 in DOM order", async () => {
    const { default: WallContainer } = await import("../WallContainer");
    const { container } = render(React.createElement(WallContainer));
    const ch5 = container.querySelector('[data-chapter="05"]');
    const ch6 = container.querySelector('[data-chapter="06"]');
    expect(ch5).toBeInTheDocument();
    expect(ch6).toBeInTheDocument();
    // compareDocumentPosition: bit 4 (0x04) means ch5 precedes ch6.
    expect(ch5!.compareDocumentPosition(ch6!) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it("Ch9 renders AFTER Ch6 in DOM order", async () => {
    const { default: WallContainer } = await import("../WallContainer");
    const { container } = render(React.createElement(WallContainer));
    const ch6 = container.querySelector('[data-chapter="06"]');
    const ch9 = container.querySelector('[data-chapter="09"]');
    expect(ch6).toBeInTheDocument();
    expect(ch9).toBeInTheDocument();
    expect(ch6!.compareDocumentPosition(ch9!) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it("Ch6 receives `active=true` when current chapter is 6", async () => {
    chapterMock = { currentChapter: 6, chapterProgress: 0.5, totalProgress: 0.55 };
    const heard: string[] = [];
    function listener(e: Event) {
      heard.push((e as CustomEvent<string>).detail);
    }
    window.addEventListener("gowork:aria-announce", listener);
    try {
      const { default: WallContainer } = await import("../WallContainer");
      render(React.createElement(WallContainer));
      // Ch6 announces its aria narration only when active. The content
      // comes from `wall.chapter06.aria` in i18n EN; assert on a stable
      // substring ("Math") that uniquely identifies Ch6.
      expect(
        heard.some((m) => typeof m === "string" && /Math/i.test(m)),
      ).toBe(true);
    } finally {
      window.removeEventListener("gowork:aria-announce", listener);
    }
  });

  it("Ch9 receives `active=true` when current chapter is 9", async () => {
    chapterMock = { currentChapter: 9, chapterProgress: 0.5, totalProgress: 0.85 };
    const heard: string[] = [];
    function listener(e: Event) {
      heard.push((e as CustomEvent<string>).detail);
    }
    window.addEventListener("gowork:aria-announce", listener);
    try {
      const { default: WallContainer } = await import("../WallContainer");
      render(React.createElement(WallContainer));
      expect(
        heard.some((m) => typeof m === "string" && /Any City/i.test(m)),
      ).toBe(true);
    } finally {
      window.removeEventListener("gowork:aria-announce", listener);
    }
  });
});

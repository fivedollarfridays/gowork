/**
 * W3 Driver B — WallContainer slot 7 + 8 wiring (T3.16).
 *
 * Slot 7 = Ch7 The Path. Slot 8 = Ch8 The Graph.
 * Other drivers handle slots 6, 9, 10. We must NOT touch them.
 */
import React from "react";
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { render, cleanup } from "@testing-library/react";

vi.mock("../MapboxScene", () => ({
  default: () => React.createElement("div", { "data-testid": "mapbox-scene-stub" }),
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

vi.mock("next/dynamic", () => ({
  default: (loader: () => Promise<{ default: React.ComponentType }>) => {
    let Component: React.ComponentType | null = null;
    void loader().then((mod) => {
      Component = mod.default;
    });
    const Wrapper: React.FC<Record<string, unknown>> = (props) => {
      if (Component) return React.createElement(Component, props);
      return React.createElement("div", { "data-testid": "dynamic-pending" });
    };
    return Wrapper;
  },
}));

// Mock @react-three/fiber so Ch8 → BarrierConstellation works headless.
vi.mock("@react-three/fiber", () => ({
  Canvas: ({ children }: React.PropsWithChildren) =>
    React.createElement("div", { "data-testid": "r3f-canvas" }, children),
  useFrame: () => undefined,
}));

let chapterMock = { currentChapter: 7, chapterProgress: 0.5, totalProgress: 0.65 };

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
  chapterMock = { currentChapter: 7, chapterProgress: 0.5, totalProgress: 0.65 };
});

afterEach(() => {
  cleanup();
  delete process.env.NEXT_PUBLIC_MAPBOX_TOKEN;
});

describe("W3 Driver B — WallContainer composes Ch7 + Ch8 in DOM order", () => {
  it("renders Ch7 (the path)", async () => {
    const { default: WallContainer } = await import("../WallContainer");
    const { container } = render(React.createElement(WallContainer));
    expect(container.querySelector('[data-chapter="07"]')).toBeInTheDocument();
  });

  it("renders Ch8 (the graph)", async () => {
    chapterMock = { currentChapter: 8, chapterProgress: 0.5, totalProgress: 0.75 };
    const { default: WallContainer } = await import("../WallContainer");
    const { container } = render(React.createElement(WallContainer));
    expect(container.querySelector('[data-chapter="08"]')).toBeInTheDocument();
  });

  it("Ch7 appears before Ch8 in DOM order", async () => {
    const { default: WallContainer } = await import("../WallContainer");
    const { container } = render(React.createElement(WallContainer));
    const all = container.querySelectorAll("[data-chapter]");
    const orders: string[] = [];
    all.forEach((el) => {
      const v = el.getAttribute("data-chapter");
      if (v === "07" || v === "08") orders.push(v);
    });
    expect(orders.indexOf("07")).toBeLessThan(orders.indexOf("08"));
  });

  it("Ch7 + Ch8 do not crash when totalProgress is 0 (orphan render)", async () => {
    chapterMock = { currentChapter: 1, chapterProgress: 0, totalProgress: 0 };
    const { default: WallContainer } = await import("../WallContainer");
    expect(() => render(React.createElement(WallContainer))).not.toThrow();
  });
});

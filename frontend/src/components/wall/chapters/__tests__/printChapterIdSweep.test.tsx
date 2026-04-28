/**
 * T4.D.4 — Print stylesheet sweep: every chapter must emit
 * `data-chapter-id` so `print.css`'s `section[data-chapter-id]` page-break
 * rule applies.
 *
 * Driver D Wave 4 added `data-chapter-id` to chapters 4, 5, 6, 9, 10
 * (Driver A had already wired 1, 2, 3, 7, 8). This sweep test pins all
 * ten so a future driver doesn't drop the attribute and silently break
 * print pagination.
 *
 * Mocks are minimal — chapters render as static markup; we don't mount
 * Three.js or Mapbox or any data-fetcher.
 */

import React from "react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { render, cleanup } from "@testing-library/react";

// Translations + reduced-motion are mocked across the full sweep.
vi.mock("@/hooks/useTranslation", () => ({
  useTranslation: () => ({
    t: (key: string) => key,
    locale: "en",
    switchLocale: vi.fn(),
  }),
  TranslationProvider: ({ children }: { children: React.ReactNode }) => (
    <>{children}</>
  ),
}));
vi.mock("@/hooks/usePrefersReducedMotion", () => ({
  usePrefersReducedMotion: () => true,
}));

// Hooks consumed by individual chapters that we don't want firing.
vi.mock("@/hooks/useVariableFontWeight", () => ({
  useVariableFontWeight: () => '"wght" 700',
}));
vi.mock("@/hooks/useHeroFontWeight", () => ({
  useHeroFontWeight: () => '"wght" 700',
  useChapterHeadingFontWeight: () => '"wght" 600',
}));
vi.mock("@/hooks/useChapterProgress", () => ({
  useChapterProgress: () => ({ currentChapter: 1, chapterProgress: 0 }),
}));
vi.mock("@/lib/wall/sound", () => ({
  play: vi.fn(),
  playSound: vi.fn(),
  preloadSounds: vi.fn(),
  isMuted: () => true,
  setMuted: vi.fn(),
  preload: vi.fn(),
}));
vi.mock("@/components/wall/AriaLiveRegion", () => ({
  useAriaLive: () => ({ announce: vi.fn() }),
  useAriaAnnounce: () => vi.fn(),
  AriaLiveProvider: ({ children }: { children: React.ReactNode }) => (
    <>{children}</>
  ),
  AriaLiveRegion: () => null,
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn(), back: vi.fn() }),
  usePathname: () => "/",
  useSearchParams: () => new URLSearchParams(),
}));

vi.mock("@/components/wall/ChapterScaffold", () => ({
  ChapterScaffold: ({ children, chapterNumber }: { children?: React.ReactNode; chapterNumber?: number }) => (
    <div data-testid={`scaffold-${chapterNumber ?? "x"}`}>{children}</div>
  ),
}));

vi.mock("@/components/wall/dev/PerformanceHUD", () => ({
  PerformanceHUD: () => null,
}));

vi.mock("@/components/wall/CarlosAvatar", () => ({
  CarlosAvatar: () => null,
}));

vi.mock("@/components/wall/BarrierConstellation", () => ({
  BarrierConstellation: () => <div data-testid="barrier-constellation-stub" />,
}));

afterEach(() => {
  cleanup();
});

describe("T4.D.4 — every chapter component emits data-chapter-id", () => {
  it("Ch1 Continental emits data-chapter-id", async () => {
    const { Chapter01Continental } = await import("../Chapter01Continental");
    const { container } = render(<Chapter01Continental progress={0} />);
    expect(container.querySelector("[data-chapter-id]")).not.toBeNull();
  });

  it("Ch2 CityArrival emits data-chapter-id", async () => {
    const { Chapter02CityArrival } = await import("../Chapter02CityArrival");
    const { container } = render(<Chapter02CityArrival progress={0} />);
    expect(container.querySelector("[data-chapter-id]")).not.toBeNull();
  });

  it("Ch3 Neighborhood emits data-chapter-id", async () => {
    const { Chapter03Neighborhood } = await import("../Chapter03Neighborhood");
    const { container } = render(
      <Chapter03Neighborhood progress={0} active={false} />,
    );
    expect(container.querySelector("[data-chapter-id]")).not.toBeNull();
  });

  it("Ch4 TheWall emits data-chapter-id", async () => {
    const { Chapter04TheWall } = await import("../Chapter04TheWall");
    const { container } = render(<Chapter04TheWall progress={0} />);
    expect(container.querySelector("[data-chapter-id]")).not.toBeNull();
  });

  it("Ch5 Labyrinth emits data-chapter-id", async () => {
    const { Chapter05Labyrinth } = await import("../Chapter05Labyrinth");
    const { container } = render(<Chapter05Labyrinth progress={0} />);
    expect(container.querySelector("[data-chapter-id]")).not.toBeNull();
  });

  it("Ch6 TheMath emits data-chapter-id", async () => {
    const { Chapter06TheMath } = await import("../Chapter06TheMath");
    const { container } = render(
      <Chapter06TheMath progress={0} active={false} />,
    );
    expect(container.querySelector("[data-chapter-id]")).not.toBeNull();
  });

  it("Ch7 ThePath emits data-chapter-id", async () => {
    const { Chapter07ThePath } = await import("../Chapter07ThePath");
    const { container } = render(
      <Chapter07ThePath progress={0} active={false} chapterNumber={7} />,
    );
    expect(container.querySelector("[data-chapter-id]")).not.toBeNull();
  });

  it("Ch8 TheGraph emits data-chapter-id", async () => {
    const { Chapter08TheGraph } = await import("../Chapter08TheGraph");
    const { container } = render(
      <Chapter08TheGraph progress={0} active={false} chapterNumber={8} />,
    );
    expect(container.querySelector("[data-chapter-id]")).not.toBeNull();
  });

  it("Ch9 AnyCity emits data-chapter-id", async () => {
    const { Chapter09AnyCity } = await import("../Chapter09AnyCity");
    const { container } = render(
      <Chapter09AnyCity progress={0} active={false} />,
    );
    expect(container.querySelector("[data-chapter-id]")).not.toBeNull();
  });

  it("Ch10 FindYourPath emits data-chapter-id", async () => {
    const { Chapter10FindYourPath } = await import("../Chapter10FindYourPath");
    const { container } = render(
      <Chapter10FindYourPath progress={0} active={false} />,
    );
    expect(container.querySelector("[data-chapter-id]")).not.toBeNull();
  });
});

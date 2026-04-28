/**
 * T2.19, T2.21, T2.22, T2.62 — Chapter 01 Continental render tests.
 *
 * Driver-coordination: this chapter is **scaffold-agnostic**. It accepts
 * a `progress` prop (0..1 within-chapter) and an optional `chapterId`
 * for ARIA-live announcements; Driver A's WallContainer wires the prop
 * via context and wraps the chapter in ChapterScaffold. Building the
 * chapter without depending on ChapterScaffold lets W2 ship + tests
 * isolate.
 */

import { describe, it, expect, vi, afterEach } from "vitest";
import { render } from "@testing-library/react";
import { Chapter01Continental } from "../Chapter01Continental";

vi.mock("@/hooks/usePrefersReducedMotion", () => ({
  usePrefersReducedMotion: vi.fn(() => false),
}));

vi.mock("@/hooks/useTranslation", () => ({
  useTranslation: vi.fn(() => ({
    locale: "en",
    t: (key: string) => {
      if (key === "wall.ch1.hero") return "What's standing between you and a job?";
      if (key === "wall.ch1.subhero")
        return "You shouldn't have to figure out the wall. We do the math, sequence the path, and hand you the plan.";
      if (key === "wall.ch1.ariaLive") return "Chapter 1: Continental — top-down view of America";
      if (key === "wall.ch1.title") return "Chapter 1 — Continental";
      return key;
    },
    switchLocale: vi.fn(),
  })),
}));

import { usePrefersReducedMotion } from "@/hooks/usePrefersReducedMotion";

afterEach(() => {
  vi.mocked(usePrefersReducedMotion).mockReturnValue(false);
});

describe("Chapter01Continental — render", () => {
  it("renders the locked hero question from i18n", () => {
    const { getByText } = render(<Chapter01Continental progress={0.5} />);
    expect(
      getByText("What's standing between you and a job?"),
    ).toBeInTheDocument();
  });

  it("renders the locked subhero copy", () => {
    const { getByText } = render(<Chapter01Continental progress={0.5} />);
    expect(
      getByText(/You shouldn't have to figure out the wall/),
    ).toBeInTheDocument();
  });

  it("emits an ARIA-live announcement region", () => {
    const { container } = render(<Chapter01Continental progress={0} />);
    const live = container.querySelector('[aria-live]');
    expect(live).not.toBeNull();
  });

  it("uses an h1 heading (Ch1 owns the page hero h1; T2.55)", () => {
    const { container } = render(<Chapter01Continental progress={0.5} />);
    const h1s = container.querySelectorAll("h1");
    expect(h1s.length).toBe(1);
  });

  it("variable font weight axis ties to scroll progress (interpolated)", () => {
    const { container, rerender } = render(<Chapter01Continental progress={0} />);
    const heading = container.querySelector("h1");
    const startVar = heading?.style.fontVariationSettings ?? "";
    rerender(<Chapter01Continental progress={1} />);
    const endVar = container.querySelector("h1")?.style.fontVariationSettings ?? "";
    expect(startVar).not.toBe(endVar);
  });
});

describe("Chapter01Continental — reduced-motion", () => {
  it("locks the variable font weight when reduced-motion is on", () => {
    vi.mocked(usePrefersReducedMotion).mockReturnValue(true);
    const { container, rerender } = render(<Chapter01Continental progress={0} />);
    const startVar = container.querySelector("h1")?.style.fontVariationSettings ?? "";
    rerender(<Chapter01Continental progress={1} />);
    const endVar = container.querySelector("h1")?.style.fontVariationSettings ?? "";
    expect(startVar).toBe(endVar);
  });

  it("renders overlay at full opacity when reduced-motion is on", () => {
    vi.mocked(usePrefersReducedMotion).mockReturnValue(true);
    const { container } = render(<Chapter01Continental progress={0} />);
    const overlay = container.querySelector('[data-testid="ch1-overlay"]') as HTMLElement | null;
    expect(overlay).not.toBeNull();
    expect(overlay?.dataset.fallback).toBe("static");
  });
});

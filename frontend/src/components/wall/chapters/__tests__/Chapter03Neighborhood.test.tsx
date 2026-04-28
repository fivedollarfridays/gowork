/**
 * T2.27, T2.29, T2.62 — Chapter 03 Neighborhood render tests.
 */

import { describe, it, expect, vi, afterEach, beforeEach } from "vitest";
import { render } from "@testing-library/react";
import { Chapter03Neighborhood } from "../Chapter03Neighborhood";

vi.mock("@/hooks/usePrefersReducedMotion", () => ({
  usePrefersReducedMotion: vi.fn(() => false),
}));

vi.mock("@/lib/wall/sound", () => ({
  play: vi.fn(),
  isMuted: vi.fn(() => false),
}));

vi.mock("@/hooks/useTranslation", () => ({
  useTranslation: vi.fn(() => ({
    locale: "en",
    t: (key: string) => {
      if (key === "wall.chapter03.body")
        return "Carlos is 29. ZIP 76119. Single father of one daughter, four years old. Recently released — sentence complete, three years past. He has $300 in cash, no vehicle, and four years of warehouse and forklift experience. He is ready to work. Four barriers stand between him and a paycheck.";
      if (key === "wall.chapter03.aria")
        return "Chapter 3: a neighborhood block in 76119. Carlos is introduced.";
      if (key === "wall.chapter03.title") return "Chapter 3 — The Neighborhood";
      return key;
    },
    switchLocale: vi.fn(),
  })),
}));

import { usePrefersReducedMotion } from "@/hooks/usePrefersReducedMotion";
import * as sound from "@/lib/wall/sound";

beforeEach(() => {
  vi.mocked(sound.play).mockClear();
  vi.mocked(sound.isMuted).mockReturnValue(false);
});

afterEach(() => {
  vi.mocked(usePrefersReducedMotion).mockReturnValue(false);
});

describe("Chapter03Neighborhood — render", () => {
  it("renders the 60-word Carlos intro from i18n", () => {
    const { getByText } = render(<Chapter03Neighborhood progress={0.5} active />);
    expect(getByText(/Carlos is 29/)).toBeInTheDocument();
    expect(getByText(/four years of warehouse/)).toBeInTheDocument();
  });

  it("uses h2 (T2.55 — only Ch1 owns h1)", () => {
    const { container } = render(<Chapter03Neighborhood progress={0.5} active />);
    expect(container.querySelectorAll("h1").length).toBe(0);
    expect(container.querySelectorAll("h2").length).toBe(1);
  });

  it("emits an ARIA-live region with chapter announcement", () => {
    const { container } = render(<Chapter03Neighborhood progress={0} active />);
    const live = container.querySelector("[aria-live]");
    expect(live).not.toBeNull();
  });

  it("emits ZIP boundary opacity attribute Driver A reads (0 → 0.3 over progress)", () => {
    const { container, rerender } = render(
      <Chapter03Neighborhood progress={0} active />,
    );
    const start = parseFloat(
      (
        container.querySelector('[data-testid="ch3-overlay"]') as HTMLElement
      ).dataset.zipFillOpacity ?? "",
    );
    rerender(<Chapter03Neighborhood progress={1} active />);
    const end = parseFloat(
      (
        container.querySelector('[data-testid="ch3-overlay"]') as HTMLElement
      ).dataset.zipFillOpacity ?? "",
    );
    expect(start).toBeCloseTo(0, 2);
    expect(end).toBeCloseTo(0.3, 2);
  });

  it("Carlos pin opacity drops in around progress 0.5 with spring (T2.27 AC)", () => {
    const { container } = render(<Chapter03Neighborhood progress={0.5} active />);
    const overlay = container.querySelector(
      '[data-testid="ch3-overlay"]',
    ) as HTMLElement;
    const opacity = parseFloat(overlay.dataset.carlosPinOpacity ?? "");
    expect(opacity).toBeGreaterThan(0);
  });
});

describe("Chapter03Neighborhood — sound trigger", () => {
  it("plays footstep on chapter enter (active=true after inactive)", () => {
    const { rerender } = render(
      <Chapter03Neighborhood progress={0} active={false} />,
    );
    expect(vi.mocked(sound.play)).not.toHaveBeenCalled();
    rerender(<Chapter03Neighborhood progress={0.05} active />);
    expect(vi.mocked(sound.play)).toHaveBeenCalledWith("footstep");
  });

  it("does NOT play sound when muted (W1 mute respected)", () => {
    vi.mocked(sound.isMuted).mockReturnValue(true);
    const { rerender } = render(
      <Chapter03Neighborhood progress={0} active={false} />,
    );
    rerender(<Chapter03Neighborhood progress={0.05} active />);
    expect(vi.mocked(sound.play)).not.toHaveBeenCalled();
  });

  it("does NOT replay sound on subsequent re-renders within the same enter", () => {
    const { rerender } = render(
      <Chapter03Neighborhood progress={0} active={false} />,
    );
    rerender(<Chapter03Neighborhood progress={0.05} active />);
    rerender(<Chapter03Neighborhood progress={0.5} active />);
    rerender(<Chapter03Neighborhood progress={0.9} active />);
    expect(vi.mocked(sound.play)).toHaveBeenCalledTimes(1);
  });
});

describe("Chapter03Neighborhood — reduced-motion", () => {
  it("Carlos pin reveals instantly at progress 0", () => {
    vi.mocked(usePrefersReducedMotion).mockReturnValue(true);
    const { container } = render(
      <Chapter03Neighborhood progress={0} active />,
    );
    const overlay = container.querySelector(
      '[data-testid="ch3-overlay"]',
    ) as HTMLElement;
    expect(overlay.dataset.fallback).toBe("static");
    expect(parseFloat(overlay.dataset.carlosPinOpacity ?? "")).toBeCloseTo(1, 2);
  });

  it("ZIP fill opacity is final from start (T2.115 — data layers visible immediately)", () => {
    vi.mocked(usePrefersReducedMotion).mockReturnValue(true);
    const { container } = render(
      <Chapter03Neighborhood progress={0} active />,
    );
    const overlay = container.querySelector(
      '[data-testid="ch3-overlay"]',
    ) as HTMLElement;
    expect(parseFloat(overlay.dataset.zipFillOpacity ?? "")).toBeCloseTo(0.3, 2);
  });
});

/**
 * T2.23, T2.25, T2.26, T2.62 — Chapter 02 City Arrival render tests.
 */

import { describe, it, expect, vi, afterEach } from "vitest";
import { render } from "@testing-library/react";
import { Chapter02CityArrival } from "../Chapter02CityArrival";

vi.mock("@/hooks/usePrefersReducedMotion", () => ({
  usePrefersReducedMotion: vi.fn(() => false),
}));

vi.mock("@/hooks/useTranslation", () => ({
  useTranslation: vi.fn(() => ({
    locale: "en",
    t: (key: string) => {
      if (key === "wall.ch2.body")
        return "Carlos lives here. ZIP 76119. East of downtown — past Sundance Square, past the courthouse.";
      if (key === "wall.ch2.ariaLive")
        return "Chapter 2: City Arrival — Fort Worth at altitude";
      if (key === "wall.ch2.title") return "Chapter 2 — City Arrival";
      return key;
    },
    switchLocale: vi.fn(),
  })),
}));

import { usePrefersReducedMotion } from "@/hooks/usePrefersReducedMotion";

afterEach(() => {
  vi.mocked(usePrefersReducedMotion).mockReturnValue(false);
});

describe("Chapter02CityArrival — render", () => {
  it("renders editorial body copy from i18n", () => {
    const { getByText } = render(<Chapter02CityArrival progress={0.5} />);
    expect(getByText(/Carlos lives here\. ZIP 76119/)).toBeInTheDocument();
  });

  it("uses h2 (T2.55 — only Ch1 owns h1)", () => {
    const { container } = render(<Chapter02CityArrival progress={0.5} />);
    expect(container.querySelectorAll("h1").length).toBe(0);
    expect(container.querySelectorAll("h2").length).toBe(1);
  });

  it("emits an ARIA-live region for the chapter title", () => {
    const { container } = render(<Chapter02CityArrival progress={0} />);
    const live = container.querySelector("[aria-live]");
    expect(live).not.toBeNull();
  });

  it("exposes the trinity-metro layer-opacity hook for Driver A's MapboxScene", () => {
    const { container } = render(<Chapter02CityArrival progress={0.5} />);
    const overlay = container.querySelector(
      '[data-testid="ch2-overlay"]',
    ) as HTMLElement | null;
    expect(overlay?.dataset.transitOpacity).toBeTruthy();
    // 0..1 numeric.
    const v = parseFloat(overlay?.dataset.transitOpacity ?? "");
    expect(v).toBeGreaterThanOrEqual(0);
    expect(v).toBeLessThanOrEqual(1);
  });

  it("scroll-tied transit opacity goes from 0 → 0.6 across progress (T2.23 AC)", () => {
    const { container, rerender } = render(<Chapter02CityArrival progress={0} />);
    const start = parseFloat(
      (
        container.querySelector('[data-testid="ch2-overlay"]') as HTMLElement
      ).dataset.transitOpacity ?? "",
    );
    rerender(<Chapter02CityArrival progress={1} />);
    const end = parseFloat(
      (
        container.querySelector('[data-testid="ch2-overlay"]') as HTMLElement
      ).dataset.transitOpacity ?? "",
    );
    expect(start).toBeLessThan(end);
    expect(end).toBeCloseTo(0.6, 2);
  });
});

describe("Chapter02CityArrival — reduced-motion", () => {
  it("transit opacity is full from the start (no scroll-tied fade)", () => {
    vi.mocked(usePrefersReducedMotion).mockReturnValue(true);
    const { container } = render(<Chapter02CityArrival progress={0} />);
    const overlay = container.querySelector(
      '[data-testid="ch2-overlay"]',
    ) as HTMLElement | null;
    expect(overlay?.dataset.fallback).toBe("static");
    const v = parseFloat(overlay?.dataset.transitOpacity ?? "");
    expect(v).toBeCloseTo(0.6, 2);
  });
});

/**
 * T4.D.1 — Hero font weight wiring (Wave 2).
 *
 * Driver A shipped `useHeroFontWeight(globalProgress)` returning a weight
 * that climbs 700→900 across global scroll 0→0.05. The chapter freeze is
 * lifted in W4 Driver D, so Ch1 now consumes globalProgress through a new
 * optional prop and applies the hero font weight to the headline.
 *
 * Contract:
 *   - When `globalProgress` is undefined, the chapter falls back to the
 *     legacy `useVariableFontWeight(progress)` behavior (zero-regression).
 *   - When `globalProgress` is defined, the headline `fontVariationSettings`
 *     is computed from `useHeroFontWeight(globalProgress)`.
 *   - Reduced motion locks to 700 regardless of `globalProgress`.
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
    t: (key: string) => key,
    switchLocale: vi.fn(),
  })),
}));

import { usePrefersReducedMotion } from "@/hooks/usePrefersReducedMotion";

afterEach(() => {
  vi.mocked(usePrefersReducedMotion).mockReturnValue(false);
});

function getHeading(container: HTMLElement): HTMLElement {
  const h1 = container.querySelector("h1");
  if (!h1) throw new Error("Chapter 1 heading not found");
  return h1 as HTMLElement;
}

describe("T4.D.1 — Chapter01 hero font weight wiring (globalProgress)", () => {
  it("at globalProgress=0 emits hero weight 700", () => {
    const { container } = render(
      <Chapter01Continental progress={0.5} globalProgress={0} />,
    );
    const h1 = getHeading(container);
    expect(h1.style.fontVariationSettings).toBe('"wght" 700');
  });

  it("at globalProgress=0.05 emits hero weight 900", () => {
    const { container } = render(
      <Chapter01Continental progress={0.5} globalProgress={0.05} />,
    );
    const h1 = getHeading(container);
    expect(h1.style.fontVariationSettings).toBe('"wght" 900');
  });

  it("at globalProgress=0.025 emits a midway weight (~800)", () => {
    const { container } = render(
      <Chapter01Continental progress={0.5} globalProgress={0.025} />,
    );
    const h1 = getHeading(container);
    expect(h1.style.fontVariationSettings).toBe('"wght" 800');
  });

  it("globalProgress past the trigger (e.g. 0.9) clamps at 900", () => {
    const { container } = render(
      <Chapter01Continental progress={0.5} globalProgress={0.9} />,
    );
    const h1 = getHeading(container);
    expect(h1.style.fontVariationSettings).toBe('"wght" 900');
  });

  it("reduced-motion locks weight to 700 even at globalProgress=0.05", () => {
    vi.mocked(usePrefersReducedMotion).mockReturnValue(true);
    const { container } = render(
      <Chapter01Continental progress={0.5} globalProgress={0.05} />,
    );
    const h1 = getHeading(container);
    expect(h1.style.fontVariationSettings).toBe('"wght" 700');
  });

  it("when globalProgress is undefined, falls back to legacy local-progress font (no regression)", () => {
    // Without globalProgress the heading should still render with a valid
    // fontVariationSettings string (the legacy useVariableFontWeight path).
    const { container } = render(<Chapter01Continental progress={0.0} />);
    const h1 = getHeading(container);
    expect(h1.style.fontVariationSettings).toMatch(/"wght" \d+/);
  });
});

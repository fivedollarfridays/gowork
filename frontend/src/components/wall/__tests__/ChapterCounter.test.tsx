/**
 * W1 Driver C — T1.52 ChapterCounter.
 *
 * Sticky top-right, format "01/10", monospace tabular nums. The component
 * is presentational : current chapter and total are passed in as props
 * (Driver B's chapter-state hook owns the source of truth).
 */
import { describe, it, expect, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { TranslationProvider } from "@/hooks/useTranslation";
import { setLocale } from "@/lib/i18n";
import { ChapterCounter } from "../ChapterCounter";

function wrap(node: React.ReactNode) {
  return render(<TranslationProvider>{node}</TranslationProvider>);
}

describe("ChapterCounter (T1.52)", () => {
  beforeEach(() => setLocale("en"));

  it("renders the 01/10 format with leading zero on single digits", () => {
    wrap(<ChapterCounter current={1} total={10} />);
    expect(screen.getByText("01")).toBeInTheDocument();
    expect(screen.getByText("10")).toBeInTheDocument();
  });

  it("renders 07/10 mid-stream", () => {
    wrap(<ChapterCounter current={7} total={10} />);
    expect(screen.getByText("07")).toBeInTheDocument();
  });

  it("renders 10/10 at the close (no extra zero on two-digit values)", () => {
    wrap(<ChapterCounter current={10} total={10} />);
    expect(screen.getAllByText("10").length).toBe(2);
  });

  it("declares an aria-label sourced from i18n for screen readers", () => {
    wrap(<ChapterCounter current={3} total={10} />);
    const region = screen.getByRole("status");
    expect(region).toHaveAttribute("aria-label");
  });

  it("uses tabular nums via the font-feature-settings class", () => {
    const { container } = wrap(<ChapterCounter current={1} total={10} />);
    const counter = container.querySelector('[data-counter]');
    expect(counter).toBeInTheDocument();
    expect(counter?.className).toMatch(/tabular-nums|tabular_nums/);
  });
});

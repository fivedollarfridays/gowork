/**
 * ChapterRail — left fixed vertical list of 8 chapter ticks + scroll
 * progress bar. Sprint/gowork-facelift Driver A.
 */
import { describe, it, expect, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { TranslationProvider } from "@/hooks/useTranslation";
import { setLocale } from "@/lib/i18n";
import { ChapterRail } from "../ChapterRail";

function wrap(node: React.ReactNode) {
  return render(<TranslationProvider>{node}</TranslationProvider>);
}

describe("ChapterRail — structure", () => {
  beforeEach(() => {
    setLocale("en");
  });

  it("renders without crashing as a navigation landmark", () => {
    wrap(<ChapterRail activeChapter={1} progress={0} />);
    expect(screen.getByRole("navigation", { name: /chapter navigation/i })).toBeInTheDocument();
  });

  it("renders all 8 chapter ticks", () => {
    wrap(<ChapterRail activeChapter={1} progress={0} />);
    const items = screen.getAllByRole("listitem");
    expect(items).toHaveLength(8);
  });

  it("marks the active chapter via aria-current=true", () => {
    wrap(<ChapterRail activeChapter={3} progress={0.4} />);
    const active = screen.getByRole("link", { name: /meet carlos/i });
    expect(active).toHaveAttribute("aria-current", "true");
  });

  it("renders chapter numbers in 01..08 zero-padded form", () => {
    const { container } = wrap(<ChapterRail activeChapter={1} progress={0} />);
    const numbers = container.querySelectorAll("[data-chapter-number]");
    expect(numbers[0]?.textContent).toBe("01");
    expect(numbers[7]?.textContent).toBe("08");
  });

  it("sets the progress bar fill width via inline style", () => {
    const { container } = wrap(<ChapterRail activeChapter={2} progress={0.5} />);
    const fill = container.querySelector("[data-progress-fill]") as HTMLElement | null;
    expect(fill).toBeTruthy();
    expect(fill?.style.height).toBe("50%");
  });
});

describe("ChapterRail — i18n", () => {
  beforeEach(() => {
    setLocale("en");
  });

  it("translates chapter labels into Spanish", () => {
    setLocale("es");
    wrap(<ChapterRail activeChapter={1} progress={0} />);
    expect(screen.getByText(/conoce a carlos/i)).toBeInTheDocument();
  });
});

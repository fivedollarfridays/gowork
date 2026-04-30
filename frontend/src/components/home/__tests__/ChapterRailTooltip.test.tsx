/**
 * ChapterRailTooltip — polish-2 T3.
 *
 * Hover/focus a chapter-rail tick → glass tooltip slides out 200×96
 * showing chapter screenshot + eyebrow.
 */
import { describe, it, expect, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { TranslationProvider } from "@/hooks/useTranslation";
import { setLocale } from "@/lib/i18n";
import { ChapterRail } from "../ChapterRail";

function wrap(node: React.ReactNode) {
  return render(<TranslationProvider>{node}</TranslationProvider>);
}

describe("ChapterRailTooltip — preview on hover/focus", () => {
  beforeEach(() => {
    setLocale("en");
  });

  it("does NOT render any tooltip at rest", () => {
    wrap(<ChapterRail activeChapter={1} progress={0} />);
    expect(screen.queryByRole("tooltip")).toBeNull();
  });

  it("renders a tooltip with the chapter-3 thumbnail when ch3 tick is hovered", () => {
    const { container } = wrap(<ChapterRail activeChapter={1} progress={0} />);
    const tick3 = container.querySelector('[data-chapter-id="3"]') as HTMLElement;
    expect(tick3).toBeTruthy();
    fireEvent.mouseEnter(tick3);
    const tooltip = screen.getByRole("tooltip");
    expect(tooltip).toBeInTheDocument();
    const img = tooltip.querySelector("img") as HTMLImageElement | null;
    expect(img).toBeTruthy();
    expect(img!.getAttribute("src")).toMatch(/chapter-thumbs\/03-meet-carlos\.jpg/);
  });

  it("renders the chapter-7 thumbnail with the wage-cliff filename", () => {
    const { container } = wrap(<ChapterRail activeChapter={1} progress={0} />);
    const tick7 = container.querySelector('[data-chapter-id="7"]') as HTMLElement;
    fireEvent.mouseEnter(tick7);
    const img = screen.getByRole("tooltip").querySelector("img") as HTMLImageElement;
    expect(img.getAttribute("src")).toMatch(/chapter-thumbs\/07-wage-cliff\.jpg/);
  });

  it("hides the tooltip on mouseleave", () => {
    const { container } = wrap(<ChapterRail activeChapter={1} progress={0} />);
    const tick3 = container.querySelector('[data-chapter-id="3"]') as HTMLElement;
    fireEvent.mouseEnter(tick3);
    expect(screen.getByRole("tooltip")).toBeInTheDocument();
    fireEvent.mouseLeave(tick3);
    expect(screen.queryByRole("tooltip")).toBeNull();
  });

  it("opens the tooltip on focus (keyboard reach)", () => {
    const { container } = wrap(<ChapterRail activeChapter={1} progress={0} />);
    const link = container.querySelector(
      '[data-chapter-id="4"] a',
    ) as HTMLElement;
    fireEvent.focus(link);
    expect(screen.getByRole("tooltip")).toBeInTheDocument();
  });

  it("renders the chapter eyebrow text in the tooltip", () => {
    const { container } = wrap(<ChapterRail activeChapter={1} progress={0} />);
    const tick3 = container.querySelector('[data-chapter-id="3"]') as HTMLElement;
    fireEvent.mouseEnter(tick3);
    const tooltip = screen.getByRole("tooltip");
    // The chapter rail label for ch3 is "Meet Carlos" (en).
    expect(tooltip.textContent?.toLowerCase()).toContain("meet carlos");
  });
});

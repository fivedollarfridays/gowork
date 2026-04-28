/**
 * W1 Driver C — T1.47 / T1.49 TitleSequence.
 *
 * The 4-second page-load title sequence :
 *   - "GoWork presents"  fades in (1s)
 *   - "The Wall"          types in letter-by-letter (2s)
 *   - "An interactive map of Fort Worth, Texas · April 2026"
 *                         fades in (1s)
 *
 * Per the dispatch :
 *   - Reduced-motion : instant title display (no typewriter, no fades).
 *   - Total: 4s (consumers can override via `durationMs` prop for tests).
 *   - When complete, calls onComplete (so consumers know to start
 *     Mapbox / chapter scroll).
 */
import { describe, it, expect, beforeEach, vi, afterEach } from "vitest";
import { render, screen, act } from "@testing-library/react";
import { TranslationProvider } from "@/hooks/useTranslation";
import { setLocale } from "@/lib/i18n";
import { TitleSequence } from "../TitleSequence";

function wrap(node: React.ReactNode) {
  return render(<TranslationProvider>{node}</TranslationProvider>);
}

describe("TitleSequence (T1.47)", () => {
  beforeEach(() => {
    setLocale("en");
    vi.useFakeTimers();
  });
  afterEach(() => {
    vi.useRealTimers();
  });

  it("renders the presenter, title, and subtitle from i18n", () => {
    wrap(<TitleSequence reducedMotion />);
    expect(screen.getByText(/gowork presents/i)).toBeInTheDocument();
    expect(screen.getByText(/the wall/i)).toBeInTheDocument();
    expect(
      screen.getByText(/interactive map of fort worth/i),
    ).toBeInTheDocument();
  });

  it("when reducedMotion is true, all three texts are visible immediately", () => {
    wrap(<TitleSequence reducedMotion />);
    const subtitle = screen.getByText(/interactive map of fort worth/i);
    expect(subtitle).toBeVisible();
  });

  it("calls onComplete after the configured duration", () => {
    const onComplete = vi.fn();
    wrap(<TitleSequence durationMs={400} onComplete={onComplete} />);
    expect(onComplete).not.toHaveBeenCalled();
    act(() => {
      vi.advanceTimersByTime(450);
    });
    expect(onComplete).toHaveBeenCalledTimes(1);
  });

  it("calls onComplete immediately when reducedMotion is true", () => {
    const onComplete = vi.fn();
    wrap(<TitleSequence reducedMotion onComplete={onComplete} />);
    act(() => {
      vi.advanceTimersByTime(0);
    });
    expect(onComplete).toHaveBeenCalledTimes(1);
  });

  it("renders Spanish copy when locale is es", () => {
    setLocale("es");
    wrap(<TitleSequence reducedMotion />);
    expect(screen.getByText(/gowork presenta/i)).toBeInTheDocument();
    expect(screen.getByText(/el muro/i)).toBeInTheDocument();
  });

  it("declares aria-live=polite on the wrapping element so AT can read the sequence", () => {
    const { container } = wrap(<TitleSequence reducedMotion />);
    const wrapper = container.querySelector("[data-title-sequence]");
    expect(wrapper).toHaveAttribute("aria-live", "polite");
  });
});

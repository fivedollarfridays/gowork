/**
 * Narrative Reset (sprint/narrative-reset) — T-Reset.4 — StartNowCTA tests.
 *
 * The StartNowCTA is a persistent floating "Start now" button that
 * surfaces from Ch1 onward. The original wall narrative buried the
 * primary CTA inside Ch10 — a user had to scroll past 10 chapters to
 * find it. The site is a job-finding tool first; the CTA must be
 * visible from the moment the user finishes the hero.
 *
 * Contract:
 *   - Visible AFTER the hero (~10% scroll). Hidden on the hero itself.
 *   - Click → routes to `/assess` (existing assessment form).
 *   - Mobile: bottom-fixed; desktop: top-right.
 *   - Reduced-motion: still visible — no fade animation.
 *   - Persists through all chapters until clicked / route changes.
 *   - Keyboard accessible; aria-label sourced from i18n.
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, cleanup } from "@testing-library/react";
import { StartNowCTA } from "../StartNowCTA";

const mockPush = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush, replace: vi.fn(), back: vi.fn() }),
}));

beforeEach(() => {
  cleanup();
  mockPush.mockReset();
});

describe("StartNowCTA — visibility gating by scroll progress", () => {
  it("is hidden when scrollProgress < threshold (Ch1 hero)", () => {
    render(<StartNowCTA scrollProgress={0.02} />);
    // The component MUST hide on Ch1 hero so the headline can breathe.
    const cta = screen.queryByTestId("start-now-cta");
    if (cta) {
      // If still in the DOM, it must carry data-visible="false".
      expect(cta.getAttribute("data-visible")).toBe("false");
    }
  });

  it("is visible past the threshold (after ~10% scroll)", () => {
    render(<StartNowCTA scrollProgress={0.15} />);
    const cta = screen.getByTestId("start-now-cta");
    expect(cta.getAttribute("data-visible")).toBe("true");
  });

  it("stays visible across all subsequent chapters", () => {
    const { rerender } = render(<StartNowCTA scrollProgress={0.2} />);
    expect(
      screen.getByTestId("start-now-cta").getAttribute("data-visible"),
    ).toBe("true");
    rerender(<StartNowCTA scrollProgress={0.5} />);
    expect(
      screen.getByTestId("start-now-cta").getAttribute("data-visible"),
    ).toBe("true");
    rerender(<StartNowCTA scrollProgress={0.99} />);
    expect(
      screen.getByTestId("start-now-cta").getAttribute("data-visible"),
    ).toBe("true");
  });
});

describe("StartNowCTA — click navigates to /assess", () => {
  it("clicking the CTA routes to /assess", () => {
    render(<StartNowCTA scrollProgress={0.5} />);
    fireEvent.click(screen.getByTestId("start-now-cta"));
    expect(mockPush).toHaveBeenCalledWith("/assess");
  });

  it("renders as a <button> for keyboard reach", () => {
    render(<StartNowCTA scrollProgress={0.5} />);
    expect(screen.getByTestId("start-now-cta").tagName).toBe("BUTTON");
  });

  it("has an accessible label from i18n", () => {
    render(<StartNowCTA scrollProgress={0.5} />);
    const cta = screen.getByTestId("start-now-cta");
    const label = cta.getAttribute("aria-label") ?? cta.textContent ?? "";
    expect(label.trim().length).toBeGreaterThan(0);
  });
});

describe("StartNowCTA — reduced-motion contract", () => {
  it("renders without fade animation when reducedMotion=true", () => {
    render(<StartNowCTA scrollProgress={0.5} reducedMotion />);
    const cta = screen.getByTestId("start-now-cta");
    expect(cta.getAttribute("data-reduced-motion")).toBe("true");
  });

  it("still visible in reduced-motion mode past the threshold", () => {
    render(<StartNowCTA scrollProgress={0.5} reducedMotion />);
    const cta = screen.getByTestId("start-now-cta");
    expect(cta.getAttribute("data-visible")).toBe("true");
  });
});

describe("StartNowCTA — placement", () => {
  it("declares data-position attribute (default 'top-right' on desktop)", () => {
    render(<StartNowCTA scrollProgress={0.5} />);
    const cta = screen.getByTestId("start-now-cta");
    const pos = cta.getAttribute("data-position");
    expect(pos === "top-right" || pos === "bottom").toBe(true);
  });

  it("supports forced position prop for tests", () => {
    render(<StartNowCTA scrollProgress={0.5} position="bottom" />);
    expect(
      screen.getByTestId("start-now-cta").getAttribute("data-position"),
    ).toBe("bottom");
  });
});

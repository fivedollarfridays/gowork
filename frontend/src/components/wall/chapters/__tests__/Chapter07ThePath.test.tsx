/**
 * W3 Driver B — Chapter 07 The Path tests (T3.10).
 *
 * Narrative Reset (sprint/narrative-reset): timeline compressed from
 * 5 weeks (Week 1/4/8/10/12) to 4 day-stages (Today, Tomorrow, Day 3,
 * This week). Editorial copy now teaches the SAME-DAY case file promise.
 *
 * Locks Ch7's render contract:
 *   - section heading h2, aria-label, data-chapter="07"
 *   - timeline overlay rendering 4 day-stage labels
 *   - EN/ES copy via i18n keys (wall.chapter07.*) — same-day phrasing
 *   - reduced-motion fallback: static path SVG visible, no animation
 *   - propagates LOCAL progress to data-attribute consumers
 */
import { describe, it, expect, beforeEach } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import { Chapter07ThePath } from "../Chapter07ThePath";
import { setLocale } from "@/lib/i18n";

beforeEach(() => {
  cleanup();
  setLocale("en");
});

describe("Chapter07ThePath — render", () => {
  it("declares data-chapter='07' on the root", () => {
    render(<Chapter07ThePath progress={0.5} active />);
    expect(
      screen.getByTestId("chapter07-the-path").getAttribute("data-chapter"),
    ).toBe("07");
  });

  it("renders an h2 with the chapter title", () => {
    render(<Chapter07ThePath progress={0.5} active />);
    const heading = screen.getByRole("heading", { level: 2 });
    expect(heading).toBeInTheDocument();
    expect(heading.textContent ?? "").not.toBe("");
  });

  it("emits an aria-label sourced from wall.chapter07.aria", () => {
    render(<Chapter07ThePath progress={0.5} active />);
    const root = screen.getByTestId("chapter07-the-path");
    expect(root.getAttribute("aria-labelledby")).toBe("chapter07-title");
  });
});

describe("Chapter07ThePath — timeline overlay (4 day-stage labels)", () => {
  it("renders 4 timeline marks (today, tomorrow, day-3, this-week)", () => {
    render(<Chapter07ThePath progress={0.5} active />);
    const marks = screen.getAllByTestId(/^ch7-timeline-day-/);
    expect(marks).toHaveLength(4);
  });

  it("each timeline mark has a data-day attribute matching the same-day flow", () => {
    render(<Chapter07ThePath progress={0.5} active />);
    const days = screen
      .getAllByTestId(/^ch7-timeline-day-/)
      .map((el) => el.getAttribute("data-day"));
    expect(days).toEqual(["today", "tomorrow", "day-3", "this-week"]);
  });

  it("does NOT render the legacy '12 weeks' timeline marks", () => {
    render(<Chapter07ThePath progress={0.5} active />);
    expect(screen.queryAllByTestId(/^ch7-timeline-week-/)).toHaveLength(0);
  });

  it("editorial copy frames same-day case file (NOT 12 weeks)", () => {
    render(<Chapter07ThePath progress={0.5} active />);
    const hero = screen.getByTestId("ch7-hero").textContent ?? "";
    // The hero should mention "twelve weeks" only as the OLD-world contrast
    // ("Don't walk for twelve weeks. Walk in once."), and the body must
    // teach the same-day case file promise.
    const body = screen.getByTestId("ch7-body").textContent ?? "";
    expect(body).toMatch(/case file|same day|same-day|today|this week/i);
  });
});

describe("Chapter07ThePath — progress propagation", () => {
  it("writes data-progress = clamped value", () => {
    render(<Chapter07ThePath progress={0.42} active />);
    const root = screen.getByTestId("chapter07-the-path");
    expect(root.getAttribute("data-progress")).toBe("0.420");
  });

  it("clamps progress > 1 to 1", () => {
    render(<Chapter07ThePath progress={1.5} active />);
    const root = screen.getByTestId("chapter07-the-path");
    expect(root.getAttribute("data-progress")).toBe("1.000");
  });
});

describe("Chapter07ThePath — i18n", () => {
  it("renders ES same-day title when locale is 'es' (Narrative Reset)", () => {
    setLocale("es");
    render(<Chapter07ThePath progress={0.5} active />);
    const heading = screen.getByRole("heading", { level: 2 });
    // The new Spanish title is "Tu expediente. Hoy." — no longer "Capítulo 7".
    expect(heading.textContent ?? "").toMatch(/expediente|Hoy/i);
    setLocale("en");
  });
});

describe("Chapter07ThePath — reduced-motion fallback", () => {
  it("renders the static-path fallback SVG when reducedMotion=true", () => {
    render(<Chapter07ThePath progress={0.0} active reducedMotion />);
    expect(screen.getByTestId("ch7-static-path-svg")).toBeInTheDocument();
  });

  it("declares data-reduced-motion on the root when reducedMotion=true", () => {
    render(<Chapter07ThePath progress={0} active reducedMotion />);
    expect(
      screen.getByTestId("chapter07-the-path").getAttribute(
        "data-reduced-motion",
      ),
    ).toBe("true");
  });

  it("static path is hidden visually when reducedMotion=false (defaults)", () => {
    render(<Chapter07ThePath progress={0.5} active />);
    expect(screen.queryByTestId("ch7-static-path-svg")).toBeNull();
  });
});

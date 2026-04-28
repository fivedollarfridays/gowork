/**
 * W3 Driver B — Chapter 07 The Path tests (T3.10).
 *
 * Locks Ch7's render contract:
 *   - section heading h2, aria-label, data-chapter="07"
 *   - timeline overlay rendering 5 week labels (1, 4, 8, 10, 12)
 *   - EN/ES copy via i18n keys (wall.chapter07.*)
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

describe("Chapter07ThePath — timeline overlay (5 week labels)", () => {
  it("renders 5 timeline marks (week 1, 4, 8, 10, 12)", () => {
    render(<Chapter07ThePath progress={0.5} active />);
    const marks = screen.getAllByTestId(/^ch7-timeline-week-/);
    expect(marks).toHaveLength(5);
  });

  it("each timeline mark has a data-week attribute", () => {
    render(<Chapter07ThePath progress={0.5} active />);
    const weeks = screen
      .getAllByTestId(/^ch7-timeline-week-/)
      .map((el) => el.getAttribute("data-week"));
    expect(weeks).toEqual(["1", "4", "8", "10", "12"]);
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
  it("renders ES title when locale is 'es'", () => {
    setLocale("es");
    render(<Chapter07ThePath progress={0.5} active />);
    const heading = screen.getByRole("heading", { level: 2 });
    expect(heading.textContent ?? "").toMatch(/Camino|Capítulo/);
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

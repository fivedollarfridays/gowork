/**
 * W2 Driver C — Chapter05Labyrinth (T2.41 + T2.42 + T2.45).
 *
 * The labyrinth chapter:
 *   - 5 office pins (Driver B layer) light up in sequence
 *   - chaotic SVG path animates between them
 *   - 47-form counter ticks 0 → 47 with progress
 *   - editorial "5 offices. 47 forms." (locked phrase)
 *   - paper-rustle audio fires on each office light-up
 *   - data-cliff toggles at counter ≥ 30 (foreshadows W3)
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { Chapter05Labyrinth } from "../Chapter05Labyrinth";
import { setLocale } from "@/lib/i18n";
import * as soundLib from "@/lib/wall/sound";

describe("Chapter05Labyrinth — copy + counter", () => {
  beforeEach(() => setLocale("en"));

  it("renders the locked editorial phrase", () => {
    render(<Chapter05Labyrinth progress={0.1} />);
    expect(screen.getByTestId("ch5-editorial").textContent).toContain(
      "5 offices",
    );
    expect(screen.getByTestId("ch5-editorial").textContent).toContain(
      "47 forms",
    );
  });

  it("renders 0 in the forms counter at progress=0", () => {
    render(<Chapter05Labyrinth progress={0} />);
    expect(screen.getByTestId("forms-counter-value").textContent).toBe("0");
  });

  it("renders 47 in the forms counter at progress=1", () => {
    render(<Chapter05Labyrinth progress={1} />);
    expect(screen.getByTestId("forms-counter-value").textContent).toBe("47");
  });

  it("declares data-chapter='05' on its root", () => {
    render(<Chapter05Labyrinth progress={0.5} />);
    expect(
      screen.getByTestId("chapter05-labyrinth").getAttribute("data-chapter"),
    ).toBe("05");
  });

  it("renders Spanish editorial when locale is es", () => {
    setLocale("es");
    render(<Chapter05Labyrinth progress={0.1} />);
    expect(screen.getByTestId("ch5-editorial").textContent).toContain(
      "5 oficinas",
    );
    setLocale("en");
  });
});

describe("Chapter05Labyrinth — office light-up sequencing", () => {
  it("emits one office light-up entry per office (5 total)", () => {
    render(<Chapter05Labyrinth progress={1} />);
    const offices = screen.getAllByTestId(/^ch5-office-/);
    expect(offices).toHaveLength(5);
  });

  it("lights offices progressively as progress grows", () => {
    const { rerender } = render(<Chapter05Labyrinth progress={0.1} />);
    const lit10 = screen
      .getAllByTestId(/^ch5-office-/)
      .filter((n) => n.getAttribute("data-lit") === "true").length;
    expect(lit10).toBe(1);

    rerender(<Chapter05Labyrinth progress={0.5} />);
    const lit50 = screen
      .getAllByTestId(/^ch5-office-/)
      .filter((n) => n.getAttribute("data-lit") === "true").length;
    expect(lit50).toBeGreaterThanOrEqual(2);

    rerender(<Chapter05Labyrinth progress={1} />);
    const lit100 = screen
      .getAllByTestId(/^ch5-office-/)
      .filter((n) => n.getAttribute("data-lit") === "true").length;
    expect(lit100).toBe(5);
  });
});

describe("Chapter05Labyrinth — sound + a11y", () => {
  let playSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    playSpy = vi.spyOn(soundLib, "play").mockImplementation(() => undefined);
  });

  afterEach(() => {
    playSpy.mockRestore();
  });

  it("plays paper-rustle on chapter entry", () => {
    render(<Chapter05Labyrinth progress={0.05} />);
    expect(playSpy).toHaveBeenCalledWith("paper-rustle");
  });

  it("dispatches the chapter aria-live narration on entry", () => {
    const heard: string[] = [];
    function listener(e: Event) {
      const detail = (e as CustomEvent<string>).detail;
      if (typeof detail === "string") heard.push(detail);
    }
    window.addEventListener("gowork:aria-announce", listener);
    try {
      render(<Chapter05Labyrinth progress={0.05} />);
      expect(heard.some((m) => m.includes("Labyrinth"))).toBe(true);
    } finally {
      window.removeEventListener("gowork:aria-announce", listener);
    }
  });

  it("renders a chaotic path SVG with stroke-dashoffset tied to progress", () => {
    render(<Chapter05Labyrinth progress={0.5} />);
    const path = screen.getByTestId("ch5-labyrinth-path");
    // Path is drawn in proportion to progress — at 0.5 it should be HALF.
    const dashoffset = path.getAttribute("stroke-dashoffset");
    expect(dashoffset).not.toBeNull();
    // jsdom returns the literal string we set.
    expect(Number(dashoffset)).toBeGreaterThan(0);
  });

  it("declares aria-hidden on the decorative path SVG", () => {
    render(<Chapter05Labyrinth progress={0.5} />);
    const svg = screen.getByTestId("ch5-labyrinth-svg");
    expect(svg.getAttribute("aria-hidden")).toBe("true");
  });
});

describe("Chapter05Labyrinth — reduced motion", () => {
  it("snaps the forms counter when reducedMotion is set", () => {
    render(<Chapter05Labyrinth progress={1} reducedMotion />);
    expect(screen.getByTestId("forms-counter-value").textContent).toBe("47");
    expect(
      screen.getByTestId("forms-counter").getAttribute("data-reduced-motion"),
    ).toBe("true");
  });

  it("renders the path fully drawn when reducedMotion is set", () => {
    render(<Chapter05Labyrinth progress={0.1} reducedMotion />);
    const path = screen.getByTestId("ch5-labyrinth-path");
    expect(path.getAttribute("stroke-dashoffset")).toBe("0");
  });
});

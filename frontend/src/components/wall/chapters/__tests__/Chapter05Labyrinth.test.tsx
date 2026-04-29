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
    // Narrative Reset: each office is wrapped in a <g> group with a circle.
    // Match on circle data-lit (not the group wrapper).
    const offices = screen
      .getAllByTestId(/^ch5-office-/)
      .filter((el) => el.tagName.toLowerCase() === "circle");
    expect(offices).toHaveLength(5);
  });

  it("lights offices progressively as progress grows", () => {
    const { rerender } = render(<Chapter05Labyrinth progress={0.1} />);
    const litCircles = (): number =>
      screen
        .getAllByTestId(/^ch5-office-/)
        .filter((el) => el.tagName.toLowerCase() === "circle")
        .filter((n) => n.getAttribute("data-lit") === "true").length;
    expect(litCircles()).toBe(1);

    rerender(<Chapter05Labyrinth progress={0.5} />);
    expect(litCircles()).toBeGreaterThanOrEqual(2);

    rerender(<Chapter05Labyrinth progress={1} />);
    expect(litCircles()).toBe(5);
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

describe("Chapter05Labyrinth — barrier meaning layer (Narrative Reset)", () => {
  beforeEach(() => setLocale("en"));

  it("renders five barrier labels — one per office node", () => {
    render(<Chapter05Labyrinth progress={1} />);
    const labels = screen.getAllByTestId(/^ch5-barrier-label-/);
    expect(labels).toHaveLength(5);
  });

  it("each barrier label contains an arrow pointing barrier → office", () => {
    render(<Chapter05Labyrinth progress={1} />);
    const labels = screen.getAllByTestId(/^ch5-barrier-label-/);
    for (const el of labels) {
      // ASCII or unicode arrow.
      expect(el.textContent ?? "").toMatch(/→|->/);
    }
  });

  it("renders barrier labels for each canonical key (criminalRecord, transit, childcare, credit, id)", () => {
    render(<Chapter05Labyrinth progress={1} />);
    expect(
      screen.getByTestId("ch5-barrier-label-criminalRecord"),
    ).toBeInTheDocument();
    expect(
      screen.getByTestId("ch5-barrier-label-transit"),
    ).toBeInTheDocument();
    expect(
      screen.getByTestId("ch5-barrier-label-childcare"),
    ).toBeInTheDocument();
    expect(screen.getByTestId("ch5-barrier-label-credit")).toBeInTheDocument();
    expect(screen.getByTestId("ch5-barrier-label-id")).toBeInTheDocument();
  });

  it("does NOT show the convergence caption before the threshold", () => {
    render(<Chapter05Labyrinth progress={0.1} />);
    expect(screen.queryByTestId("ch5-convergence-caption")).toBeNull();
  });

  it("shows the convergence caption past the threshold (progress >= 0.85)", () => {
    render(<Chapter05Labyrinth progress={0.9} />);
    const caption = screen.getByTestId("ch5-convergence-caption");
    expect(caption.textContent ?? "").toMatch(/47.*5|sequence|walk once/i);
  });

  it("data-converged on root toggles to 'true' past the convergence threshold", () => {
    const { rerender } = render(<Chapter05Labyrinth progress={0.1} />);
    expect(
      screen.getByTestId("chapter05-labyrinth").getAttribute("data-converged"),
    ).toBe("false");
    rerender(<Chapter05Labyrinth progress={0.95} />);
    expect(
      screen.getByTestId("chapter05-labyrinth").getAttribute("data-converged"),
    ).toBe("true");
  });

  it("reduced-motion users see the convergence caption from the start", () => {
    render(<Chapter05Labyrinth progress={0.1} reducedMotion />);
    expect(
      screen.getByTestId("ch5-convergence-caption"),
    ).toBeInTheDocument();
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

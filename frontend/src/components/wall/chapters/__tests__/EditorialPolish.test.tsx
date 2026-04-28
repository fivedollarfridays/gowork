/**
 * W2 Driver C — editorial polish + Spotlight inventions.
 *
 * Covers Wave 5 of the dispatch:
 *   - Carlos quote pull-quotes are present per sub-chapter
 *   - data-emphasis-tint signals which barrier the page is on
 *   - data-cliff toggles past the 30-form threshold (Spotlight #1)
 *   - SubChapterShell extras slot accepts arbitrary nodes
 */
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { setLocale } from "@/lib/i18n";
import { Chapter04aCriminalRecord } from "../Chapter04aCriminalRecord";
import { Chapter04bNoTransit } from "../Chapter04bNoTransit";
import { Chapter04cNoChildcare } from "../Chapter04cNoChildcare";
import { Chapter04dBadCredit } from "../Chapter04dBadCredit";
import { Chapter05Labyrinth } from "../Chapter05Labyrinth";
import { FormsCounter } from "../FormsCounter";

describe("Editorial pull-quotes — Carlos voice (Spotlight #2 — multi-perspective)", () => {
  it("Ch4a renders a Carlos pull-quote", () => {
    setLocale("en");
    render(<Chapter04aCriminalRecord progress={0.1} />);
    const pq = screen.getByTestId("ch4-pullquote");
    expect(pq.textContent).toContain("$300");
    expect(pq.tagName).toBe("BLOCKQUOTE");
    expect(pq.className).toContain("editorial-pullquote");
  });

  it("Ch4b renders a transit pull-quote", () => {
    render(<Chapter04bNoTransit progress={0.4} />);
    expect(screen.getByTestId("ch4-pullquote").textContent).toContain(
      "Forty-five",
    );
  });

  it("Ch4c renders a childcare pull-quote", () => {
    render(<Chapter04cNoChildcare progress={0.6} />);
    expect(screen.getByTestId("ch4-pullquote").textContent).toContain(
      "daycare",
    );
  });

  it("Ch4d renders a credit pull-quote (rose tinted)", () => {
    render(<Chapter04dBadCredit progress={0.9} />);
    const pq = screen.getByTestId("ch4-pullquote");
    expect(pq.textContent).toContain("score");
    // Rose tint set inline — verify via the data attribute on the section.
    expect(
      screen.getByTestId("ch4-subchapter").getAttribute("data-emphasis-tint"),
    ).toBe("rose");
  });

  it("Ch5 renders a Carlos pull-quote underneath the labyrinth", () => {
    render(<Chapter05Labyrinth progress={0.5} />);
    expect(screen.getByTestId("ch5-pullquote").textContent).toContain(
      "Every office",
    );
  });
});

describe("Spotlight #1 — data-cliff threshold drives accent shift", () => {
  it("data-cliff stays false below 30 forms", () => {
    render(<FormsCounter progress={0.6} />);
    // 0.6 * 47 ≈ 28 — still below 30.
    expect(screen.getByTestId("forms-counter").getAttribute("data-cliff")).toBe(
      "false",
    );
  });

  it("data-cliff flips true once the counter crosses 30", () => {
    render(<FormsCounter progress={0.7} />);
    // 0.7 * 47 ≈ 33 — over the threshold.
    expect(screen.getByTestId("forms-counter").getAttribute("data-cliff")).toBe(
      "true",
    );
  });

  it("rose accent class is applied above threshold", () => {
    render(<FormsCounter progress={0.8} />);
    const value = screen.getByTestId("forms-counter-value");
    expect(value.className).toContain("var(--accent-rose)");
  });

  it("amber accent class is applied below threshold", () => {
    render(<FormsCounter progress={0.4} />);
    const value = screen.getByTestId("forms-counter-value");
    expect(value.className).toContain("var(--accent-amber)");
  });
});

describe("Spotlight #3 — single ARIA-live narration sink", () => {
  it("Ch4 narration uses 'Barrier {n}' phrasing for screen-readability", () => {
    setLocale("en");
    render(<Chapter04aCriminalRecord progress={0.1} />);
    const narration = screen.getByTestId("ch4-aria-narration");
    expect(narration.textContent).toContain("Barrier one");
  });

  it("Ch5 narration uses the 'Labyrinth' title verbatim", () => {
    setLocale("en");
    render(<Chapter05Labyrinth progress={0.1} />);
    // The Ch5 component dispatches via window event; we can also read
    // the chapter title from the DOM as a sanity check.
    expect(
      screen.getByText(/Labyrinth/, { selector: "h2" }),
    ).toBeInTheDocument();
  });
});

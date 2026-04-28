/**
 * W2 Driver C — FormsCounter (Ch5 47-form tally).
 *
 * Behaviour contract:
 *   - At progress 0, renders "0".
 *   - At progress 1, renders "47" (canonical W2_LABYRINTH_FORM_COUNT).
 *   - Mid-progress rounds to the nearest integer (no fractional forms).
 *   - When `reducedMotion` is true the counter snaps and never animates;
 *     when false the counter renders as a plain integer (no transitions
 *     in jsdom — animation lives in CSS variables on the parent).
 *   - The numeric region announces via aria-label "X of 47 forms".
 *   - The crossover threshold (≥30 forms) toggles `data-cliff="true"`,
 *     which the page's CSS uses to start the amber→rose accent shift.
 */
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { FormsCounter } from "../FormsCounter";

describe("FormsCounter", () => {
  it("renders 0 at progress=0", () => {
    render(<FormsCounter progress={0} />);
    expect(screen.getByTestId("forms-counter-value").textContent).toBe("0");
  });

  it("renders 47 at progress=1", () => {
    render(<FormsCounter progress={1} />);
    expect(screen.getByTestId("forms-counter-value").textContent).toBe("47");
  });

  it("rounds mid-progress to a whole-form count", () => {
    render(<FormsCounter progress={0.5} />);
    // 0.5 * 47 = 23.5 → rounds to 24
    expect(screen.getByTestId("forms-counter-value").textContent).toBe("24");
  });

  it("clamps progress > 1 to 47", () => {
    render(<FormsCounter progress={1.5} />);
    expect(screen.getByTestId("forms-counter-value").textContent).toBe("47");
  });

  it("clamps progress < 0 to 0", () => {
    render(<FormsCounter progress={-0.2} />);
    expect(screen.getByTestId("forms-counter-value").textContent).toBe("0");
  });

  it("publishes an aria-label that names the canonical total", () => {
    render(<FormsCounter progress={0.4} />);
    const node = screen.getByTestId("forms-counter");
    expect(node.getAttribute("aria-label")).toBe("19 of 47 forms");
  });

  it("toggles data-cliff='false' below the 30-form threshold", () => {
    render(<FormsCounter progress={0.5} />);
    const node = screen.getByTestId("forms-counter");
    expect(node.getAttribute("data-cliff")).toBe("false");
  });

  it("toggles data-cliff='true' once the 30-form threshold is crossed", () => {
    render(<FormsCounter progress={0.7} />);
    // 0.7 * 47 ≈ 33 → above threshold
    const node = screen.getByTestId("forms-counter");
    expect(node.getAttribute("data-cliff")).toBe("true");
  });

  it("snaps to the final value when reducedMotion is set", () => {
    render(<FormsCounter progress={1} reducedMotion />);
    expect(screen.getByTestId("forms-counter-value").textContent).toBe("47");
  });

  it("uses tabular-nums for stable digit width", () => {
    render(<FormsCounter progress={0.4} />);
    const valueNode = screen.getByTestId("forms-counter-value");
    expect(valueNode.className).toContain("tabular-nums");
  });
});

/**
 * W3 Driver A — Chapter 06 The Math (T3.1, T3.2, T3.3, T3.8).
 *
 * The cliff-math chapter:
 *   - dark gradient overlay + EN/ES editorial copy
 *   - embedded BenefitsCliffChart (IMPORTED, never duplicated)
 *   - wage slider drives `--temperature-multiplier`
 *   - calculator-click sound on slider drag end
 *   - 71-min stat pill (Carlos's commute to DFW5 via Bus 4)
 *   - reduced-motion: no scroll-tied wage drift; user slider still works
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { setLocale } from "@/lib/i18n";
import * as soundLib from "@/lib/wall/sound";
import { Chapter06TheMath } from "../Chapter06TheMath";

describe("Chapter06TheMath — copy + structure", () => {
  beforeEach(() => setLocale("en"));

  it("renders the locked hero question from i18n", () => {
    render(<Chapter06TheMath progress={0.5} active={true} />);
    expect(screen.getByTestId("ch6-hero").textContent).toContain(
      "When more pay means less money",
    );
  });

  it("renders the locked subhero copy", () => {
    render(<Chapter06TheMath progress={0.1} active={true} />);
    expect(screen.getByTestId("ch6-subhero").textContent).toMatch(
      /cliff math/i,
    );
  });

  it("renders the 71-min stat pill (Carlos's commute to DFW5)", () => {
    render(<Chapter06TheMath progress={0.5} active={true} />);
    expect(screen.getByTestId("ch6-stat-value").textContent).toContain(
      "71 min",
    );
  });

  it("declares data-chapter='06' on its root", () => {
    render(<Chapter06TheMath progress={0.5} active={true} />);
    expect(
      screen.getByTestId("chapter06-the-math").getAttribute("data-chapter"),
    ).toBe("06");
  });

  it("uses an h2 heading with id used by aria-labelledby", () => {
    render(<Chapter06TheMath progress={0.5} active={true} />);
    const root = screen.getByTestId("chapter06-the-math");
    const h2 = root.querySelector("h2");
    expect(h2).not.toBeNull();
    expect(root.getAttribute("aria-labelledby")).toBe(h2!.id);
  });

  it("renders Spanish hero when locale is es", () => {
    setLocale("es");
    render(<Chapter06TheMath progress={0.5} active={true} />);
    expect(screen.getByTestId("ch6-hero").textContent).toContain(
      "ganar más significa tener menos",
    );
    setLocale("en");
  });
});

describe("Chapter06TheMath — embedded BenefitsCliffChart", () => {
  beforeEach(() => setLocale("en"));

  it("renders the embedded cliff chart container", () => {
    render(<Chapter06TheMath progress={0.5} active={true} />);
    expect(screen.getByTestId("ch6-cliff-chart-host")).toBeInTheDocument();
  });
});

describe("Chapter06TheMath — wage slider + temperature-multiplier", () => {
  beforeEach(() => {
    setLocale("en");
    document.documentElement.style.removeProperty("--temperature-multiplier");
  });

  it("renders a range slider with min, max, step, and default value", () => {
    render(<Chapter06TheMath progress={0.5} active={true} />);
    const slider = screen.getByTestId("ch6-wage-slider") as HTMLInputElement;
    expect(slider.type).toBe("range");
    expect(Number(slider.min)).toBeCloseTo(7.25, 5);
    expect(Number(slider.max)).toBe(25);
    expect(Number(slider.step)).toBeCloseTo(0.5, 5);
    // Default ~ $15/hr
    expect(Number(slider.value)).toBe(15);
  });

  it("slider input drives --temperature-multiplier on the chapter root", () => {
    render(<Chapter06TheMath progress={0.5} active={true} />);
    const slider = screen.getByTestId("ch6-wage-slider") as HTMLInputElement;
    const root = screen.getByTestId("chapter06-the-math") as HTMLElement;

    // Default state — temperature-multiplier set on initial render.
    const initial = root.style.getPropertyValue("--temperature-multiplier");
    expect(initial).not.toBe("");

    fireEvent.input(slider, { target: { value: "25" } });
    const atMax = root.style.getPropertyValue("--temperature-multiplier");
    expect(parseFloat(atMax)).toBeCloseTo(2.5, 5);

    fireEvent.input(slider, { target: { value: "7.25" } });
    const atMin = root.style.getPropertyValue("--temperature-multiplier");
    expect(parseFloat(atMin)).toBeCloseTo(1.0, 5);
  });

  it("slider has visible min/max/current labels", () => {
    render(<Chapter06TheMath progress={0.5} active={true} />);
    expect(screen.getByTestId("ch6-wage-slider-min").textContent).toContain(
      "$7.25",
    );
    expect(screen.getByTestId("ch6-wage-slider-max").textContent).toContain(
      "$25",
    );
    expect(screen.getByTestId("ch6-wage-slider-value").textContent).toContain(
      "$",
    );
  });

  it("slider has accessible name via aria-label or aria-labelledby", () => {
    render(<Chapter06TheMath progress={0.5} active={true} />);
    const slider = screen.getByTestId("ch6-wage-slider");
    const labelled =
      slider.getAttribute("aria-label") ??
      slider.getAttribute("aria-labelledby");
    expect(labelled).toBeTruthy();
  });
});

describe("Chapter06TheMath — calculator-click on drag end", () => {
  let playSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    setLocale("en");
    playSpy = vi.spyOn(soundLib, "play").mockImplementation(() => undefined);
  });

  afterEach(() => {
    playSpy.mockRestore();
  });

  it("plays calculator-click on slider change (drag end)", () => {
    render(<Chapter06TheMath progress={0.5} active={true} />);
    const slider = screen.getByTestId("ch6-wage-slider");
    fireEvent.change(slider, { target: { value: "20" } });
    expect(
      playSpy.mock.calls.some(
        (args: unknown[]) => args[0] === "calculator-click",
      ),
    ).toBe(true);
  });
});

describe("Chapter06TheMath — a11y + active narration", () => {
  beforeEach(() => setLocale("en"));

  it("emits the chapter aria-live narration when active", () => {
    const heard: string[] = [];
    function listener(e: Event) {
      const detail = (e as CustomEvent<string>).detail;
      if (typeof detail === "string") heard.push(detail);
    }
    window.addEventListener("gowork:aria-announce", listener);
    try {
      render(<Chapter06TheMath progress={0.05} active={true} />);
      expect(heard.some((m) => m.includes("Math"))).toBe(true);
    } finally {
      window.removeEventListener("gowork:aria-announce", listener);
    }
  });

  it("does NOT emit narration when inactive", () => {
    const heard: string[] = [];
    function listener(e: Event) {
      heard.push((e as CustomEvent<string>).detail);
    }
    window.addEventListener("gowork:aria-announce", listener);
    try {
      render(<Chapter06TheMath progress={0.05} active={false} />);
      expect(heard.length).toBe(0);
    } finally {
      window.removeEventListener("gowork:aria-announce", listener);
    }
  });
});

describe("Chapter06TheMath — reduced-motion contract", () => {
  beforeEach(() => setLocale("en"));

  it("renders with reducedMotion data-attribute when prop is set", () => {
    render(
      <Chapter06TheMath progress={0.5} active={true} reducedMotion={true} />,
    );
    expect(
      screen
        .getByTestId("chapter06-the-math")
        .getAttribute("data-reduced-motion"),
    ).toBe("true");
  });
});

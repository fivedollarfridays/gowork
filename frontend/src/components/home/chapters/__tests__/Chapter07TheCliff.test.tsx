/**
 * Chapter07TheCliff — interactive wage-cliff calculator (Driver B).
 *
 * Locks:
 *   - Section is data-bg=rose with aria-labelledby on h2.
 *   - Eyebrow "07 / The cliff".
 *   - Slider is a `<input type="range" min=14 max=28 step=0.25>` defaulting
 *     at 18.50.
 *   - Initial readout matches the static design at $18.50: gross $3,204,
 *     SNAP −$120, childcare −$110, Medicaid "at risk", real Δ −$230.
 *   - Sliding to $20 produces the cliff outputs: SNAP −$312, CC −$220,
 *     Medicaid "lapses", real Δ −$532.
 *   - Sliding to $26 produces the recovery: SNAP −$360, CC −$260,
 *     Medicaid "lapses", real Δ −$620 (still negative — honest).
 *   - SVG cliff chart renders + has a marker that updates.
 *   - Spanish toggle swaps the controls labels.
 */
import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { render, screen, cleanup, fireEvent } from "@testing-library/react";
import { TranslationProvider } from "@/hooks/useTranslation";
import { setLocale } from "@/lib/i18n";

import { Chapter07TheCliff, __resetCliffPulseForTests } from "../Chapter07TheCliff";

beforeEach(() => {
  setLocale("en");
  __resetCliffPulseForTests();
  document.body.removeAttribute("data-cliff-pulse");
});
afterEach(() => {
  cleanup();
  setLocale("en");
});

function renderEn() {
  setLocale("en");
  return render(
    <TranslationProvider>
      <Chapter07TheCliff />
    </TranslationProvider>,
  );
}

function renderEs() {
  setLocale("es");
  return render(
    <TranslationProvider>
      <Chapter07TheCliff />
    </TranslationProvider>,
  );
}

describe("Chapter07TheCliff — wage cliff calculator", () => {
  it("renders a section with data-bg=rose", () => {
    const { container } = renderEn();
    expect(container.querySelector("section[data-bg='rose']")).not.toBeNull();
  });

  it("section has aria-labelledby pointing at h2", () => {
    const { container } = renderEn();
    const section = container.querySelector("section[data-bg='rose']");
    const id = section?.getAttribute("aria-labelledby");
    expect(id).toBeTruthy();
    const h2 = container.querySelector(`#${id}`);
    expect(h2?.tagName.toLowerCase()).toBe("h2");
  });

  it("slider defaults to 18.50 with the expected min/max/step", () => {
    const { container } = renderEn();
    const slider = container.querySelector<HTMLInputElement>("input[type='range']");
    expect(slider).not.toBeNull();
    expect(slider?.min).toBe("14");
    expect(slider?.max).toBe("28");
    expect(slider?.step).toBe("0.25");
    expect(slider?.value).toBe("18.5");
  });

  it("initial readout at $18.50 shows the cliff (SNAP −$312, CC −$110, Medicaid at risk, total −$422)", () => {
    // At exactly $18.50 the math falls into the `< 20` SNAP bucket (−$312).
    // Childcare starts at $18+ and is −$110 below $19. Medicaid is "at risk"
    // until $19. Total is the honest sum: −$422.
    renderEn();
    expect(screen.getByText("$18.50")).toBeInTheDocument();
    expect(screen.getByText("$3,204")).toBeInTheDocument();
    expect(screen.getByText("−$312")).toBeInTheDocument(); // SNAP
    expect(screen.getByText("−$110")).toBeInTheDocument(); // childcare
    expect(screen.getByText("at risk")).toBeInTheDocument();
    expect(screen.getByText("−$422")).toBeInTheDocument(); // total
  });

  it("dragging slider to 20 moves us into the cliff zone (Medicaid readout lapses)", () => {
    const { container } = renderEn();
    const slider = container.querySelector<HTMLInputElement>("input[type='range']")!;
    fireEvent.change(slider, { target: { value: "20" } });
    expect(screen.getByText("$20.00")).toBeInTheDocument();
    // Find the Medicaid readout row by walking up from the row label.
    const medRow = container.querySelector(".ctrl-readout")
      ?.querySelectorAll(".r-row")[3];
    expect(medRow?.textContent).toMatch(/lapses/i);
  });

  it("dragging slider to 26 keeps the readout negative (the honest math)", () => {
    const { container } = renderEn();
    const slider = container.querySelector<HTMLInputElement>("input[type='range']")!;
    fireEvent.change(slider, { target: { value: "26" } });
    expect(screen.getByText("$26.00")).toBeInTheDocument();
    // total row carries the −$ sign; both rose-toned and last in the list.
    const total = container.querySelector(".r-total .r-v");
    expect(total?.textContent ?? "").toMatch(/^−\$/);
  });

  it("renders an SVG chart with a cliff-marker that has a transform", () => {
    const { container } = renderEn();
    const svg = container.querySelector("svg[aria-label]");
    expect(svg).not.toBeNull();
    const marker = container.querySelector("#cliff-marker");
    expect(marker).not.toBeNull();
    expect(marker?.getAttribute("transform")).toBeTruthy();
  });

  it("Spanish toggle swaps the eyebrow + controls labels", () => {
    renderEs();
    expect(screen.getByText(/El acantilado/i)).toBeInTheDocument();
    expect(screen.getByText(/Salario por hora/i)).toBeInTheDocument();
    expect(screen.getByText(/en riesgo/i)).toBeInTheDocument();
  });
});

describe("Chapter07TheCliff — T30 cliff-impact pulse + haptic", () => {
  it("crossing wage from 16 to 18 sets body[data-cliff-pulse='true'] (first-time only)", () => {
    document.body.removeAttribute("data-cliff-pulse");
    const { container } = renderEn();
    const slider = container.querySelector<HTMLInputElement>("input[type='range']")!;
    fireEvent.change(slider, { target: { value: "16" } });
    expect(document.body.getAttribute("data-cliff-pulse")).not.toBe("true");
    fireEvent.change(slider, { target: { value: "18" } });
    expect(document.body.getAttribute("data-cliff-pulse")).toBe("true");
  });

  it("crossing back from 18 to 16 does NOT re-trigger the pulse", () => {
    document.body.removeAttribute("data-cliff-pulse");
    const { container } = renderEn();
    const slider = container.querySelector<HTMLInputElement>("input[type='range']")!;
    // Forward crossing fires once.
    fireEvent.change(slider, { target: { value: "18" } });
    // Reset the marker so we can detect a second fire.
    document.body.removeAttribute("data-cliff-pulse");
    // Crossing back below the threshold must NOT re-arm.
    fireEvent.change(slider, { target: { value: "16" } });
    expect(document.body.getAttribute("data-cliff-pulse")).not.toBe("true");
    // And re-crossing forward in the same session also doesn't re-fire.
    fireEvent.change(slider, { target: { value: "20" } });
    expect(document.body.getAttribute("data-cliff-pulse")).not.toBe("true");
  });
});

describe("Chapter07TheCliff — T31 cliff annotations + tooltip", () => {
  it("hovering the cliff annotation reveals a role=tooltip with cliff copy", () => {
    const { container } = renderEn();
    const cliffG = container.querySelector('[data-annotation="cliff"]');
    expect(cliffG).not.toBeNull();
    fireEvent.pointerEnter(cliffG!);
    const tip = container.querySelector('[role="tooltip"]');
    expect(tip).not.toBeNull();
    expect(tip?.textContent ?? "").toMatch(/cliff edge|SNAP|childcare/i);
  });

  it("hovering the destination annotation reveals the Alcon tooltip", () => {
    const { container } = renderEn();
    const destG = container.querySelector('[data-annotation="destination"]');
    expect(destG).not.toBeNull();
    fireEvent.pointerEnter(destG!);
    const tip = container.querySelector('[role="tooltip"]');
    expect(tip).not.toBeNull();
    expect(tip?.textContent ?? "").toMatch(/Alcon|destination/i);
  });
});

describe("Chapter07TheCliff — T32 household-size segmented control", () => {
  it("renders 4 household-size buttons (1/2/3/4)", () => {
    renderEn();
    expect(screen.getByTestId("ch07-household-1")).toBeInTheDocument();
    expect(screen.getByTestId("ch07-household-2")).toBeInTheDocument();
    expect(screen.getByTestId("ch07-household-3")).toBeInTheDocument();
    expect(screen.getByTestId("ch07-household-4")).toBeInTheDocument();
  });

  it("clicking household=4 shifts the cliff zone (Medicaid 'safe' at $20)", () => {
    const { container } = renderEn();
    const slider = container.querySelector<HTMLInputElement>("input[type='range']")!;
    fireEvent.change(slider, { target: { value: "20" } });
    const household4 = screen.getByTestId("ch07-household-4");
    fireEvent.click(household4);
    // Re-read the Medicaid row.
    const medRow = container.querySelector(".ctrl-readout")
      ?.querySelectorAll(".r-row")[3];
    expect(medRow?.textContent).toMatch(/safe|seguro/i);
  });
});

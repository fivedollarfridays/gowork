/**
 * Chapter07TheCliff — interactive wage-cliff calculator (narrative-reset).
 *
 * Locks (post-CliffMoneyTower rewrite):
 *   - Section is data-bg=rose with aria-labelledby on h2.
 *   - Eyebrow "07 / The cliff".
 *   - Slider is a `<input type="range" min=14 step=0.25>` defaulting at 18.50.
 *     Slider max is per-household (24/26/29/32 for HH 1/2/3/4) so each
 *     household can drag fully past its cliff edge.
 *   - Initial readout at $18.50 (HH=1): gross $3,204, SNAP −$312, CC −$110,
 *     Medicaid "at risk", total −$422.
 *   - Sliding to $20 produces the cliff outputs: Medicaid "lapses".
 *   - The CliffMoneyTower stacked-money-tower visual replaces the old SVG
 *     line chart; the readout numbers also surface inside the controls
 *     panel (so the SAME values can appear twice — use scoped queries).
 *   - Spanish toggle swaps the controls labels.
 *   - 4 household-size radio buttons + cliff threshold shifts.
 *   - T30 cliff-impact pulse + haptic on first forward crossing.
 */
import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { render, screen, cleanup, fireEvent, within } from "@testing-library/react";
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

/** Read the controls-panel readout rows, which live under .ctrl-readout. */
function readoutRows(container: HTMLElement): HTMLElement[] {
  const root = container.querySelector(".ctrl-readout");
  if (!root) return [];
  return Array.from(root.querySelectorAll<HTMLElement>(".r-row"));
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

  it("slider defaults to 18.50 with the expected min/step (max scales per household; HH=1 default = 24)", () => {
    const { container } = renderEn();
    const slider = container.querySelector<HTMLInputElement>("input[type='range']");
    expect(slider).not.toBeNull();
    expect(slider?.min).toBe("14");
    // Per-household max (sliderMaxForHousehold) gives HH=1 → 24, HH=2 → 26,
    // HH=3 → 29, HH=4 → 32. Default household is 1.
    expect(slider?.max).toBe("24");
    expect(slider?.step).toBe("0.25");
    expect(slider?.value).toBe("18.5");
  });

  it("initial readout at $18.50 shows the cliff (SNAP −$312, CC −$110, Medicaid at risk, total −$422)", () => {
    // At $18.50 the SNAP/CC/Medicaid math still falls into the same buckets
    // as before (the legend numbers haven't changed — only the visual
    // changed). The same values may appear in the money-tower visual too,
    // so we scope queries to the controls-panel readout.
    const { container } = renderEn();
    const readout = container.querySelector(".ctrl-readout") as HTMLElement;
    expect(readout).not.toBeNull();
    const within$readout = within(readout);
    expect(within$readout.getByText("$3,204")).toBeInTheDocument();
    expect(within$readout.getByText("−$312")).toBeInTheDocument(); // SNAP
    expect(within$readout.getByText("−$110")).toBeInTheDocument(); // childcare
    expect(within$readout.getByText("at risk")).toBeInTheDocument();
    expect(within$readout.getByText("−$422")).toBeInTheDocument(); // total
    // The current wage chip lives outside the readout panel; assert
    // separately (and tolerate multiple matches if the tower mirrors it).
    expect(screen.getAllByText("$18.50").length).toBeGreaterThan(0);
  });

  it("dragging slider to 20 moves us into the cliff zone (Medicaid readout lapses)", () => {
    const { container } = renderEn();
    const slider = container.querySelector<HTMLInputElement>("input[type='range']")!;
    fireEvent.change(slider, { target: { value: "20" } });
    expect(screen.getAllByText("$20.00").length).toBeGreaterThan(0);
    // The 4th readout row is the Medicaid bucket label.
    const rows = readoutRows(container);
    expect(rows[3]?.textContent ?? "").toMatch(/lapses/i);
  });

  it("dragging slider to its max keeps the readout negative (the honest math)", () => {
    // For HH=1 the slider max is 24. Drag to the upper bound and verify
    // the total row is still rendered with a leading minus (the cliff
    // recovery doesn't fully close on a single household).
    const { container } = renderEn();
    const slider = container.querySelector<HTMLInputElement>("input[type='range']")!;
    fireEvent.change(slider, { target: { value: slider.max } });
    expect(screen.getAllByText(`$${parseFloat(slider.max).toFixed(2)}`).length).toBeGreaterThan(0);
    const total = container.querySelector(".r-total .r-v");
    expect(total?.textContent ?? "").toMatch(/^−\$/);
  });

  it("renders the CliffMoneyTower stacked-money-tower visual", () => {
    // The narrative-reset replaced the SVG line-chart with a stacked-money
    // tower component. Locate it via its data-testid (or stable class) so
    // the test catches future visual regressions.
    const { container } = renderEn();
    const tower = container.querySelector("[data-cliff-tower], .ch07-tower");
    expect(tower).not.toBeNull();
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
    fireEvent.change(slider, { target: { value: "18" } });
    document.body.removeAttribute("data-cliff-pulse");
    fireEvent.change(slider, { target: { value: "16" } });
    expect(document.body.getAttribute("data-cliff-pulse")).not.toBe("true");
    fireEvent.change(slider, { target: { value: "20" } });
    expect(document.body.getAttribute("data-cliff-pulse")).not.toBe("true");
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
    const rows = readoutRows(container);
    expect(rows[3]?.textContent).toMatch(/safe|seguro/i);
  });

  it("slider max scales when household changes (HH=4 unlocks $32)", () => {
    const { container } = renderEn();
    const slider = container.querySelector<HTMLInputElement>("input[type='range']")!;
    expect(slider.max).toBe("24");
    fireEvent.click(screen.getByTestId("ch07-household-4"));
    expect(slider.max).toBe("32");
  });
});

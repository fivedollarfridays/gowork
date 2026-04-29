/**
 * Driver C — sprint/gowork-facelift Chapter 05 The Plan tests.
 *
 * Locks the contract:
 *   - section #chapter-05 with class ch05, data-bg="dark"
 *   - aria-labelledby pointing at the title
 *   - 4 plan cards (Monday/Tuesday/Wednesday/Thursday)
 *   - copy in EN + ES
 *   - reduced-motion contract: cards still render in their final state
 */
import { describe, it, expect, beforeEach } from "vitest";
import { render, screen, cleanup, fireEvent } from "@testing-library/react";
import { TranslationProvider } from "@/hooks/useTranslation";
import { setLocale } from "@/lib/i18n";
import { Chapter05ThePlan } from "../Chapter05ThePlan";

function renderEN(node: React.ReactNode) {
  setLocale("en");
  return render(<TranslationProvider>{node}</TranslationProvider>);
}
function renderES(node: React.ReactNode) {
  setLocale("es");
  return render(<TranslationProvider>{node}</TranslationProvider>);
}

beforeEach(() => {
  cleanup();
  setLocale("en");
});

describe("Chapter05ThePlan — render contract", () => {
  it("renders a section with id chapter-05 and class ch05", () => {
    renderEN(<Chapter05ThePlan />);
    const section = document.getElementById("chapter-05");
    expect(section).toBeInTheDocument();
    expect(section?.className).toMatch(/ch05/);
    expect(section?.getAttribute("data-bg")).toBe("dark");
  });

  it("declares aria-labelledby pointing at the chapter title id", () => {
    renderEN(<Chapter05ThePlan />);
    const section = document.getElementById("chapter-05");
    const labelledBy = section?.getAttribute("aria-labelledby");
    expect(labelledBy).toBeTruthy();
    expect(document.getElementById(labelledBy ?? "")).toBeInTheDocument();
  });

  it("renders 4 plan cards (Monday → Thursday)", () => {
    renderEN(<Chapter05ThePlan />);
    expect(screen.getByTestId("ch05-card-1")).toBeInTheDocument();
    expect(screen.getByTestId("ch05-card-2")).toBeInTheDocument();
    expect(screen.getByTestId("ch05-card-3")).toBeInTheDocument();
    expect(screen.getByTestId("ch05-card-4")).toBeInTheDocument();
  });

  it("each card carries its day-tag (Monday/Tuesday/Wed/Thu)", () => {
    renderEN(<Chapter05ThePlan />);
    expect(screen.getByTestId("ch05-card-1").textContent).toMatch(/Monday/i);
    expect(screen.getByTestId("ch05-card-2").textContent).toMatch(/Tuesday/i);
    expect(screen.getByTestId("ch05-card-3").textContent).toMatch(/Wednesday/i);
    expect(screen.getByTestId("ch05-card-4").textContent).toMatch(/Thursday/i);
  });

  it("each card has a numbered identifier 01..04", () => {
    renderEN(<Chapter05ThePlan />);
    expect(screen.getByTestId("ch05-card-1").textContent).toMatch(/01/);
    expect(screen.getByTestId("ch05-card-4").textContent).toMatch(/04/);
  });
});

describe("Chapter05ThePlan — i18n", () => {
  it("renders Spanish day-tags when locale = es", () => {
    renderES(<Chapter05ThePlan />);
    expect(screen.getByTestId("ch05-card-1").textContent).toMatch(/Lunes/i);
    expect(screen.getByTestId("ch05-card-2").textContent).toMatch(/Martes/i);
    expect(screen.getByTestId("ch05-card-3").textContent).toMatch(/Miércoles/i);
    expect(screen.getByTestId("ch05-card-4").textContent).toMatch(/Jueves/i);
  });

  it("renders the eyebrow '05 / The plan' in EN", () => {
    renderEN(<Chapter05ThePlan />);
    expect(
      screen.getAllByText(/05 \/ The plan/i).length,
    ).toBeGreaterThan(0);
  });
});

describe("Chapter05ThePlan — T24 hover preview-flip", () => {
  it("hovering ch05-card-2 sets data-flipped=true on that card", () => {
    renderEN(<Chapter05ThePlan />);
    const card = screen.getByTestId("ch05-card-2");
    expect(card.getAttribute("data-flipped")).toBe("false");
    fireEvent.pointerEnter(card);
    expect(card.getAttribute("data-flipped")).toBe("true");
  });

  it("pointerleave restores data-flipped=false", () => {
    renderEN(<Chapter05ThePlan />);
    const card = screen.getByTestId("ch05-card-2");
    fireEvent.pointerEnter(card);
    expect(card.getAttribute("data-flipped")).toBe("true");
    fireEvent.pointerLeave(card);
    expect(card.getAttribute("data-flipped")).toBe("false");
  });

  it("the back face renders 3 bullets (i18n keys back1/back2/back3)", () => {
    renderEN(<Chapter05ThePlan />);
    const card = screen.getByTestId("ch05-card-2");
    const back = card.querySelector('[data-face="back"]');
    expect(back).not.toBeNull();
    expect(back?.querySelectorAll("li").length).toBe(3);
  });

  it("each card has both a front and a back face", () => {
    renderEN(<Chapter05ThePlan />);
    for (const id of ["ch05-card-1", "ch05-card-2", "ch05-card-3", "ch05-card-4"]) {
      const card = screen.getByTestId(id);
      expect(card.querySelector('[data-face="front"]')).not.toBeNull();
      expect(card.querySelector('[data-face="back"]')).not.toBeNull();
    }
  });
});

describe("Chapter05ThePlan — T25 mobile horizontal scroll-snap", () => {
  it("the .ch05-fan container has scroll-snap-type set on x via CSS namespace", () => {
    // The mobile behavior is delivered via a CSS rule keyed off the
    // `[data-mobile-snap]` attribute. The component opts in by setting
    // that attribute on the fan container — the @media query in
    // home-chapters.css does the rest.
    renderEN(<Chapter05ThePlan />);
    const section = document.getElementById("chapter-05");
    const fan = section?.querySelector(".ch05-fan");
    expect(fan).not.toBeNull();
    expect(fan?.getAttribute("data-mobile-snap")).toBe("true");
  });
});

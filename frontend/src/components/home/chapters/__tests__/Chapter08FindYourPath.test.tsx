/**
 * Chapter08FindYourPath — manifesto + giant wordmark closer (Driver B).
 *
 * Locks the narrative-reset directive (commit b233102):
 *   - Section is data-bg=warm with aria-labelledby on h2.
 *   - Eyebrow "08 / Find your path".
 *   - 4-line manifesto h2 (with "be on Tuesday" final em).
 *   - CTA-XL primary "Get your plan" → /assess + meta line.
 *   - Giant wordmark "GO / WORK" with `wm-row-1` + `wm-row-2`.
 *   - **NO stat band** (no "5,189 / 13 / 2 / MIT" — narrative-reset strip).
 *   - Spanish toggle swaps eyebrow + manifesto + meta.
 */
import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import { TranslationProvider } from "@/hooks/useTranslation";
import { setLocale } from "@/lib/i18n";

import { Chapter08FindYourPath } from "../Chapter08FindYourPath";

beforeEach(() => setLocale("en"));
afterEach(() => {
  cleanup();
  setLocale("en");
});

function renderEn() {
  setLocale("en");
  return render(
    <TranslationProvider>
      <Chapter08FindYourPath />
    </TranslationProvider>,
  );
}

function renderEs() {
  setLocale("es");
  return render(
    <TranslationProvider>
      <Chapter08FindYourPath />
    </TranslationProvider>,
  );
}

describe("Chapter08FindYourPath — manifesto closer", () => {
  it("renders a section with data-bg=warm", () => {
    const { container } = renderEn();
    expect(container.querySelector("section[data-bg='warm']")).not.toBeNull();
  });

  it("section has aria-labelledby pointing at h2", () => {
    const { container } = renderEn();
    const section = container.querySelector("section[data-bg='warm']");
    const id = section?.getAttribute("aria-labelledby");
    expect(id).toBeTruthy();
    const h2 = container.querySelector(`#${id}`);
    expect(h2?.tagName.toLowerCase()).toBe("h2");
  });

  it("renders the four-line manifesto", () => {
    renderEn();
    expect(screen.getByText(/We won't fix the wall/i)).toBeInTheDocument();
    expect(screen.getByText(/We'll just keep tearing it down/i)).toBeInTheDocument();
    expect(screen.getByText(/brick by brick by brick/i)).toBeInTheDocument();
    expect(screen.getByText(/be on Tuesday/i)).toBeInTheDocument();
  });

  it("renders CTA-XL primary that points at /assess + meta line", () => {
    renderEn();
    const primary = screen.getByRole("link", { name: /Get your plan/i });
    expect(primary).toHaveAttribute("href", "/assess");
    expect(primary.className).toContain("cta-xl");
    expect(
      screen.getByText(/~3 min · web or text · in English or Spanish/i),
    ).toBeInTheDocument();
  });

  it("renders the giant wordmark with two rows GO + WORK", () => {
    const { container } = renderEn();
    expect(container.querySelector(".ch08-wordmark .wm-row-1")?.textContent).toBe("GO");
    expect(container.querySelector(".ch08-wordmark .wm-row-2")?.textContent).toBe("WORK");
  });

  it("does NOT render the deprecated stat band (narrative-reset)", () => {
    const { container } = renderEn();
    // Strip is gone per Shawn's narrative-reset directive — no "5,189",
    // no "13 sprints", no "MIT" caption from the closer.
    expect(container.querySelector(".ch08-stats")).toBeNull();
    expect(container.textContent).not.toMatch(/5,189/);
    expect(container.textContent).not.toMatch(/13 sprints/);
  });

  it("Spanish toggle swaps the manifesto + CTA meta", () => {
    renderEs();
    expect(
      screen.getByText(/No vamos a arreglar el muro/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/Obtén tu plan/i)).toBeInTheDocument();
    expect(screen.getByText(/web o texto/i)).toBeInTheDocument();
  });
});

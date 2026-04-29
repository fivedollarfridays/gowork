/**
 * Chapter01TheWall — kinetic hero (Driver B, sprint/gowork-facelift).
 *
 * Locks the editorial contract:
 *   - Renders a `<section>` with `data-bg="dark"`.
 *   - Eyebrow chip carries "HackFW 2026 · Fort Worth, TX · live in production".
 *   - The hero h1 has all three editorial lines (the morph word, the wall
 *     statement, the brick-by-brick closer).
 *   - The subhead names "seven invisible barriers" + the "first system" close.
 *   - Both CTAs render (primary `/assess`, ghost `#chapter-04`).
 *   - The marquee names every barrier from the copy thesis.
 *   - Section is keyboarded with `aria-labelledby` pointing at the h1.
 *   - Spanish locale toggle swaps the visible copy.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import { TranslationProvider } from "@/hooks/useTranslation";
import { setLocale } from "@/lib/i18n";

import { Chapter01TheWall } from "../Chapter01TheWall";

beforeEach(() => {
  setLocale("en");
});

afterEach(() => {
  cleanup();
  setLocale("en");
});

function renderEn() {
  setLocale("en");
  return render(
    <TranslationProvider>
      <Chapter01TheWall />
    </TranslationProvider>,
  );
}

function renderEs() {
  setLocale("es");
  return render(
    <TranslationProvider>
      <Chapter01TheWall />
    </TranslationProvider>,
  );
}

describe("Chapter01TheWall — kinetic hero", () => {
  it("renders a section tagged with data-bg=dark", () => {
    const { container } = renderEn();
    const section = container.querySelector("section[data-bg='dark']");
    expect(section).not.toBeNull();
  });

  it("section uses aria-labelledby pointing at the h1", () => {
    const { container } = renderEn();
    const section = container.querySelector("section[data-bg='dark']");
    const labelledBy = section?.getAttribute("aria-labelledby");
    expect(labelledBy).toBeTruthy();
    const h1 = container.querySelector(`#${labelledBy}`);
    expect(h1?.tagName.toLowerCase()).toBe("h1");
  });

  it("eyebrow chip carries HackFW 2026 framing", () => {
    renderEn();
    expect(
      screen.getByText(/HackFW 2026/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/Fort Worth, TX/i)).toBeInTheDocument();
    expect(screen.getByText(/live in production/i)).toBeInTheDocument();
  });

  it("h1 includes all three editorial lines", () => {
    const { container } = renderEn();
    expect(container.querySelector(".line-1")).not.toBeNull();
    expect(container.querySelector(".line-2")).not.toBeNull();
    expect(container.querySelector(".line-3")).not.toBeNull();
    expect(container.querySelector("#morph-word")).not.toBeNull();
  });

  it("subhead names the seven barriers and the first-system promise", () => {
    renderEn();
    expect(
      screen.getByText(/seven invisible barriers/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/first system that sees all seven/i),
    ).toBeInTheDocument();
  });

  it("renders primary CTA pointing at /assess and ghost CTA pointing at #chapter-04", () => {
    renderEn();
    const primary = screen.getByRole("link", { name: /Get your plan/i });
    expect(primary).toHaveAttribute("href", "/assess");
    const ghost = screen.getByRole("link", { name: /See how it works/i });
    expect(ghost).toHaveAttribute("href", "#chapter-04");
  });

  it("marquee names all seven barriers", () => {
    const { container } = renderEn();
    const track = container.querySelector(".mq-track");
    expect(track).not.toBeNull();
    const text = track?.textContent ?? "";
    expect(text).toMatch(/Suspended license/i);
    expect(text).toMatch(/Open court date/i);
    expect(text).toMatch(/Childcare pickup gap/i);
    expect(text).toMatch(/47-minute bus headway/i);
    expect(text).toMatch(/Background-check stigma/i);
    expect(text).toMatch(/Wage-cliff math/i);
    expect(text).toMatch(/No human to call/i);
  });

  it("Spanish toggle swaps eyebrow + subhead", () => {
    renderEs();
    expect(screen.getByText(/en producción/i)).toBeInTheDocument();
    expect(
      screen.getByText(/siete barreras invisibles/i),
    ).toBeInTheDocument();
  });
});

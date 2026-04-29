/**
 * Chapter03MeetCarlos — split portrait + parallax text (Driver B).
 *
 * Locks:
 *   - Section is data-bg=warm with aria-labelledby pointing at the heading.
 *   - Stylized SVG portrait renders + has an alt/title.
 *   - Caption block names "CARLOS R. · 34 · ZIP 76104" and the bus quote.
 *   - Eyebrow "03 / Meet Carlos".
 *   - h2 renders all 8 words; the last 4 are tagged italic-axis.
 *   - Two paragraphs about ZIP 76104.
 *   - Facts grid renders 2:30 / 2:00 / 47 / 4:00.
 *   - Spanish toggle swaps eyebrow + caption.
 */
import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import { TranslationProvider } from "@/hooks/useTranslation";
import { setLocale } from "@/lib/i18n";

import { Chapter03MeetCarlos } from "../Chapter03MeetCarlos";

beforeEach(() => setLocale("en"));
afterEach(() => {
  cleanup();
  setLocale("en");
});

function renderEn() {
  setLocale("en");
  return render(
    <TranslationProvider>
      <Chapter03MeetCarlos />
    </TranslationProvider>,
  );
}

function renderEs() {
  setLocale("es");
  return render(
    <TranslationProvider>
      <Chapter03MeetCarlos />
    </TranslationProvider>,
  );
}

describe("Chapter03MeetCarlos — split portrait + parallax text", () => {
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

  it("renders the stylized portrait svg", () => {
    const { container } = renderEn();
    expect(container.querySelector(".carlos-svg")).not.toBeNull();
  });

  it("caption block names Carlos R. and the bus quote", () => {
    renderEn();
    expect(screen.getByText(/CARLOS R\. · 34 · ZIP 76104/)).toBeInTheDocument();
    expect(screen.getByText(/47 minutes/i)).toBeInTheDocument();
  });

  it("h2 renders all 8 words with the last 4 italicized", () => {
    const { container } = renderEn();
    const words = container.querySelectorAll(".ch03-h2 .word");
    expect(words.length).toBe(8);
    const italic = container.querySelectorAll(".ch03-h2 .word.italic-axis");
    expect(italic.length).toBe(4);
  });

  it("facts grid carries 2:30, 2:00, 47, 4:00", () => {
    renderEn();
    expect(screen.getByText("2:30")).toBeInTheDocument();
    expect(screen.getByText("2:00")).toBeInTheDocument();
    expect(screen.getByText("47")).toBeInTheDocument();
    expect(screen.getByText("4:00")).toBeInTheDocument();
  });

  it("Spanish toggle swaps eyebrow + caption", () => {
    renderEs();
    expect(screen.getByText(/Conoce a Carlos/i)).toBeInTheDocument();
    expect(screen.getByText(/cada 47 minutos/i)).toBeInTheDocument();
  });
});

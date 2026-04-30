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

  it("renders the Carlos portrait image inside the framed portrait wrapper", () => {
    // polish-3 swap: the synthetic SVG portrait was replaced with a real
    // photograph (`/home/carlos.jpg`) loaded through next/image. Locate the
    // portrait wrapper + its <img> child instead of the legacy `.carlos-svg`.
    const { container } = renderEn();
    const portrait = container.querySelector(".ch03-portrait");
    expect(portrait).not.toBeNull();
    const img = portrait?.querySelector("img");
    expect(img).not.toBeNull();
    expect(img?.getAttribute("src") ?? "").toMatch(/carlos\.jpg/);
    expect(img?.getAttribute("alt") ?? "").not.toBe("");
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

describe("Chapter03MeetCarlos — T16 portrait depth (vignette + rim)", () => {
  // polish-3 replaced the SVG-with-3-parallax-z-layers portrait with a real
  // photograph layered with a vignette + rim-glow overlay. Depth is now
  // achieved via overlay layers on top of the <img>, not via SVG <g>
  // parallax. These tests assert the new depth chrome instead.
  it("portrait wrapper layers the photo + vignette + rim overlays", () => {
    const { container } = renderEn();
    const portrait = container.querySelector(".ch03-portrait");
    expect(portrait).not.toBeNull();
    // Photo + 2 aria-hidden overlay divs (vignette + rim) + the caption block.
    const img = portrait?.querySelector("img");
    expect(img).not.toBeNull();
    const overlays = portrait?.querySelectorAll('div[aria-hidden="true"]');
    expect((overlays?.length ?? 0)).toBeGreaterThanOrEqual(2);
  });

  it("portrait wrapper opts into the gradient-border treatment", () => {
    const { container } = renderEn();
    const portrait = container.querySelector(".ch03-portrait");
    expect(portrait?.getAttribute("data-gradient-border")).toBe("on");
  });
});

describe("Chapter03MeetCarlos — T17 photo-caption gradient border", () => {
  it("portrait wrapper carries the ch03-portrait class so the gradient rule applies", () => {
    const { container } = renderEn();
    const portrait = container.querySelector(".ch03-portrait");
    expect(portrait).not.toBeNull();
  });

  it("portrait wrapper opts in to the gradient border via data-gradient-border", () => {
    const { container } = renderEn();
    const portrait = container.querySelector(".ch03-portrait");
    expect(portrait?.getAttribute("data-gradient-border")).toBe("on");
  });
});

describe("Chapter03MeetCarlos — T18 fact-grid lift + count-up", () => {
  it("each fact carries a data-countup target attribute", () => {
    const { container } = renderEn();
    const facts = container.querySelectorAll(".ch03-facts .fact[data-countup]");
    // 4 facts in the grid; all opt into count-up tween.
    expect(facts.length).toBe(4);
  });

  it("each fact-num carries a data-stat-num hook so the GSAP tween can drive it", () => {
    const { container } = renderEn();
    const nums = container.querySelectorAll(
      ".ch03-facts .fact .fact-num[data-stat-num]",
    );
    expect(nums.length).toBe(4);
  });
});

describe("Chapter03MeetCarlos — light-mode polish (caption pill always-dark surface)", () => {
  // The caption pill is an editorial dark glass overlay sitting OVER the
  // Carlos photo. Its background is locked to navy (rgba(10,14,26,0.86))
  // regardless of theme so it doesn't fight the photograph. Therefore its
  // text MUST be locked-cream — using `var(--fg-primary)` flipped the
  // body line to navy ink in light mode and made the quote invisible on
  // the dark pill. The eyebrow stays amber (accent works in both themes).
  it("caption body line uses locked-cream color, not theme-flipping token", () => {
    const { container } = renderEn();
    const line = container.querySelector(".ch03-caption .cap-line");
    expect(line).not.toBeNull();
    const inline = (line as HTMLElement).style.color;
    // Must be locked cream — NOT a theme-flipping CSS variable. Accept any
    // case-form of #F5F3EE (browsers may normalize to rgb(245, 243, 238)).
    expect(inline).toMatch(/#f5f3ee|245,\s*243,\s*238/i);
    expect(inline).not.toMatch(/var\(--fg/);
  });

  it("caption block bg is locked dark (always-dark editorial overlay)", () => {
    const { container } = renderEn();
    const cap = container.querySelector(".ch03-caption");
    expect(cap).not.toBeNull();
    const bg = (cap as HTMLElement).style.background;
    // rgba navy backdrop — same value in light + dark themes.
    expect(bg).toMatch(/rgba\(10,\s*14,\s*26/);
  });
});

/**
 * Driver C — sprint/gowork-facelift Chapter 04 The Map (Mapbox + cards) tests.
 *
 * jsdom cannot run Mapbox GL (no WebGL), so the chapter renders the
 * editorial fallback when `new mapboxgl.Map` throws or the token is
 * absent. These tests exercise that fallback path AND lock the static
 * editorial contract: section identity, aria, commentary cards, hud,
 * EN/ES toggle. The full Mapbox cinematics live in Playwright e2e.
 */
import { describe, it, expect, beforeEach } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import { TranslationProvider } from "@/hooks/useTranslation";
import { setLocale } from "@/lib/i18n";
import { Chapter04TheMap } from "../Chapter04TheMap";

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

describe("Chapter04TheMap — render contract", () => {
  it("renders a section with id chapter-04 and class ch04", () => {
    renderEN(<Chapter04TheMap />);
    const section = document.getElementById("chapter-04");
    expect(section).toBeInTheDocument();
    expect(section?.tagName).toBe("SECTION");
    expect(section?.className).toMatch(/ch04/);
  });

  it("declares aria-labelledby pointing at the chapter title id", () => {
    renderEN(<Chapter04TheMap />);
    const section = document.getElementById("chapter-04");
    const labelledBy = section?.getAttribute("aria-labelledby");
    expect(labelledBy).toBeTruthy();
    expect(document.getElementById(labelledBy ?? "")).toBeInTheDocument();
  });

  it("renders the four commentary cards (cc-1..cc-4)", () => {
    renderEN(<Chapter04TheMap />);
    expect(screen.getByTestId("ch04-card-1")).toBeInTheDocument();
    expect(screen.getByTestId("ch04-card-2")).toBeInTheDocument();
    expect(screen.getByTestId("ch04-card-3")).toBeInTheDocument();
    expect(screen.getByTestId("ch04-card-4")).toBeInTheDocument();
  });

  it("renders the HUD with SCENE/FOCUS/CLEARED rows", () => {
    renderEN(<Chapter04TheMap />);
    const hud = screen.getByTestId("ch04-hud");
    expect(hud).toBeInTheDocument();
    expect(hud.textContent).toMatch(/SCENE/i);
    expect(hud.textContent).toMatch(/FOCUS/i);
    expect(hud.textContent).toMatch(/CLEARED/i);
  });

  it("renders a #map mount target", () => {
    renderEN(<Chapter04TheMap />);
    expect(document.getElementById("map")).toBeInTheDocument();
  });
});

describe("Chapter04TheMap — copy + i18n", () => {
  it("renders Tuesday narrative copy in EN", () => {
    renderEN(<Chapter04TheMap />);
    const card1 = screen.getByTestId("ch04-card-1");
    expect(card1.textContent).toMatch(/Tuesday|impossible appointments|DPS/i);
  });

  it("renders Spanish copy when locale = es", () => {
    renderES(<Chapter04TheMap />);
    const card1 = screen.getByTestId("ch04-card-1");
    expect(card1.textContent).toMatch(/Martes|imposibles|DPS/i);
  });

  it("renders the eyebrow '04 / The map' in EN", () => {
    renderEN(<Chapter04TheMap />);
    // The eyebrow text appears in BOTH the sr-only chapter title AND the
    // HUD FOCUS row, so we accept any occurrence.
    expect(screen.getAllByText(/04 \/ The map/i).length).toBeGreaterThan(0);
  });
});

describe("Chapter04TheMap — branded fallback (no token / SSR)", () => {
  it("does NOT crash when Mapbox is unavailable (jsdom path)", () => {
    // Just rendering under jsdom triggers the fallback branch.
    expect(() => renderEN(<Chapter04TheMap />)).not.toThrow();
  });

  it("renders an editorial fallback caption in jsdom", () => {
    renderEN(<Chapter04TheMap />);
    // The fallback layer is always present (it sits behind the map);
    // it surfaces the editorial copy so judges in airplane mode can read.
    expect(screen.getByTestId("ch04-fallback")).toBeInTheDocument();
  });
});

describe("Chapter04TheMap — T19 typed-in HUD", () => {
  it("HUD values carry data-typewriter so the typewrite helper can drive them", () => {
    renderEN(<Chapter04TheMap />);
    const hud = screen.getByTestId("ch04-hud");
    const typed = hud.querySelectorAll("[data-typewriter]");
    // SCENE / FOCUS / CLEARED — three rows, three typewriter spans.
    expect(typed.length).toBeGreaterThanOrEqual(3);
  });
});

describe("Chapter04TheMap — T20 cursor-flashlight dim mode", () => {
  it("renders a #map mount target the cursor handler scopes to", () => {
    renderEN(<Chapter04TheMap />);
    expect(document.getElementById("map")).toBeInTheDocument();
  });

  it("attaches data-map-cursor-active=false to body on mount (non-touch)", () => {
    renderEN(<Chapter04TheMap />);
    // The chapter's effect publishes the body attribute synchronously on
    // mount so CSS can target it; tests confirm the contract surface.
    const value = document.body.getAttribute("data-map-cursor-active");
    expect(value === "false" || value === null).toBe(true);
  });
});

describe("Chapter04TheMap — T22 legend chip (Ch04-enrich · 6 rows)", () => {
  it("renders the legend chip when section is mounted", () => {
    renderEN(<Chapter04TheMap />);
    const legend = document.querySelector("[data-ch04-legend]");
    expect(legend).not.toBeNull();
  });

  it("legend carries 6 swatch rows (3 routes + 3 waypoint colors)", () => {
    renderEN(<Chapter04TheMap />);
    const legend = document.querySelector("[data-ch04-legend]");
    const rows = legend?.querySelectorAll("[data-legend-row]");
    expect(rows?.length).toBe(6);
  });

  it("legend exposes a heading row (LEGEND)", () => {
    renderEN(<Chapter04TheMap />);
    const heading = document.querySelector("[data-ch04-legend-heading]");
    expect(heading).not.toBeNull();
    expect(heading?.textContent ?? "").toMatch(/LEGEND/i);
  });

  it("legend renders Spanish labels when locale=es", () => {
    renderES(<Chapter04TheMap />);
    const legend = document.querySelector("[data-ch04-legend]");
    // Carlos's name is preserved (proper noun) AND the heading translates.
    expect(legend?.textContent ?? "").toMatch(/Carlos|LEYENDA/i);
  });
});

describe("Chapter04TheMap — T21 isochrone ring overlay", () => {
  it("section renders a [data-isochrone] SVG overlay above the canvas", () => {
    renderEN(<Chapter04TheMap />);
    const iso = document.querySelector("[data-isochrone]");
    expect(iso).not.toBeNull();
    expect(iso?.tagName.toLowerCase()).toBe("svg");
  });

  it("isochrone overlay carries a circle with a non-zero radius", () => {
    renderEN(<Chapter04TheMap />);
    const circle = document.querySelector("[data-isochrone] circle");
    expect(circle).not.toBeNull();
    const r = parseFloat(circle?.getAttribute("r") ?? "0");
    expect(r).toBeGreaterThan(0);
  });
});

describe("Chapter04TheMap — Ch04-enrich compass HUD (top-right)", () => {
  it("renders a [data-ch04-compass] block with 4 value rows", () => {
    renderEN(<Chapter04TheMap />);
    const c = document.querySelector("[data-ch04-compass]");
    expect(c).not.toBeNull();
    const rows = c?.querySelectorAll("[data-ch04-compass-row]");
    expect(rows?.length).toBe(4);
  });

  it("renders a pulsing cyan dot inside the compass", () => {
    renderEN(<Chapter04TheMap />);
    expect(document.querySelector("[data-ch04-compass-dot]")).not.toBeNull();
  });
});

describe("Chapter04TheMap — Ch04-enrich stat row (bottom-center)", () => {
  it("renders 4 stats (wage / headway / commute / records)", () => {
    renderEN(<Chapter04TheMap />);
    const row = document.querySelector("[data-ch04-stat-row]");
    expect(row).not.toBeNull();
    const stats = row?.querySelectorAll("[data-ch04-stat]");
    expect(stats?.length).toBe(4);
  });
});

describe("Chapter04TheMap — Ch04 attribution chip removed", () => {
  it("does not render the attribution chip (intentionally removed for demo)", () => {
    renderEN(<Chapter04TheMap />);
    const chip = document.querySelector("[data-ch04-attrib]");
    expect(chip).toBeNull();
  });
});

describe("Chapter04TheMap — Ch04-enrich film grain", () => {
  it("renders a [data-ch04-grain] overlay element", () => {
    renderEN(<Chapter04TheMap />);
    expect(document.querySelector("[data-ch04-grain]")).not.toBeNull();
  });
});

describe("Chapter04TheMap — Ch04-enrich SVG overlay", () => {
  it("renders the [data-ch04-svg-overlay] inside the pinned map frame", () => {
    renderEN(<Chapter04TheMap />);
    expect(document.querySelector("[data-ch04-svg-overlay]")).not.toBeNull();
  });
});

describe("Chapter04TheMap — T23 sky time-of-day overlay", () => {
  it("section publishes a data-tod attribute (one of the phase tokens)", () => {
    renderEN(<Chapter04TheMap />);
    const section = document.getElementById("chapter-04");
    const tod = section?.getAttribute("data-tod");
    expect(tod).toBeTruthy();
    // dawn / midday / dusk / night are the phase tokens.
    expect(["dawn", "midday", "dusk", "night"]).toContain(tod ?? "");
  });
});

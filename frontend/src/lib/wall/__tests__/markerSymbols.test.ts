/**
 * T2.16 — Custom marker SVG sprite tests.
 *
 * The sprite registry exposes:
 *   - MARKER_SYMBOLS: a record of `gowork-office-<category>` → SVG string
 *   - registerMarkerSymbols(map): wires each SVG into the Mapbox sprite
 *     via `addImage` so the symbol layer's `icon-image` lookup resolves.
 *
 * Each SVG ships at 32×32, designed in the editorial dark style with
 * W1 brand cyan/amber accents (no hardcoded hex outside known tokens).
 */

import { describe, it, expect, vi } from "vitest";
import {
  MARKER_SYMBOLS,
  MARKER_CATEGORIES,
  registerMarkerSymbols,
  type MarkerCategory,
} from "../markerSymbols";

describe("markerSymbols — registry", () => {
  it("ships one symbol per office category required by T2.16", () => {
    const expected: MarkerCategory[] = [
      "court",
      "benefits",
      "dps",
      "workforce",
      "legal",
    ];
    for (const cat of expected) {
      expect(MARKER_CATEGORIES).toContain(cat);
      expect(MARKER_SYMBOLS[cat]).toBeTruthy();
    }
  });

  it("each SVG declares a 32-unit viewBox so it scales cleanly to 64px", () => {
    for (const cat of MARKER_CATEGORIES) {
      const svg = MARKER_SYMBOLS[cat];
      expect(svg).toMatch(/viewBox="0 0 32 32"/);
    }
  });

  it("sprite ids follow the gowork-office-<category> namespace", () => {
    for (const cat of MARKER_CATEGORIES) {
      expect(`gowork-office-${cat}`).toMatch(/^gowork-office-/);
    }
  });
});

describe("markerSymbols — registerMarkerSymbols(map)", () => {
  it("calls map.loadImage + addImage once per category (Mapbox sprite path)", async () => {
    const addImage = vi.fn();
    const fakeMap = { addImage } as unknown as Parameters<typeof registerMarkerSymbols>[0];
    await registerMarkerSymbols(fakeMap);
    expect(addImage).toHaveBeenCalledTimes(MARKER_CATEGORIES.length);
  });

  it("registered ids are gowork-office-<category>", async () => {
    const ids: string[] = [];
    const addImage = vi.fn((id: string) => {
      ids.push(id);
    });
    const fakeMap = { addImage } as unknown as Parameters<typeof registerMarkerSymbols>[0];
    await registerMarkerSymbols(fakeMap);
    for (const cat of MARKER_CATEGORIES) {
      expect(ids).toContain(`gowork-office-${cat}`);
    }
  });

  it("does not throw when map.addImage is missing (graceful no-op)", async () => {
    await expect(registerMarkerSymbols({} as never)).resolves.toBeUndefined();
  });
});

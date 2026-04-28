/**
 * Spotlight invention 3 — brand asset manifest (lib/wall/brandAssets.ts).
 *
 * Enumerates every brand asset (SVG, raster, font, audio) the wall ships
 * with sizes + content-types so dev tools (asset gallery, audit scripts,
 * release runbook) reach a single source of truth. Separate from the PWA
 * web manifest — that one is for browsers, this one is for our scripts.
 */
import { describe, it, expect } from "vitest";
import { BRAND_ASSETS, getAsset } from "../brandAssets";

describe("brandAssets — registry contract", () => {
  it("enumerates the canonical SVG icon", () => {
    const svg = getAsset("icon.svg");
    expect(svg).toBeDefined();
    expect(svg?.kind).toBe("svg");
    expect(svg?.path).toBe("/icon.svg");
  });

  it("enumerates 16/32/192/512 favicon rasters", () => {
    expect(getAsset("favicon-16.png")).toBeDefined();
    expect(getAsset("favicon-32.png")).toBeDefined();
    expect(getAsset("icon-192.png")).toBeDefined();
    expect(getAsset("icon-512.png")).toBeDefined();
  });

  it("enumerates the OG image", () => {
    const og = getAsset("og-image.svg");
    expect(og).toBeDefined();
    expect(og?.kind).toBe("svg");
  });

  it("includes all 5 placeholder sound effects", () => {
    const ids = [
      "footstep.mp3",
      "paper-rustle.mp3",
      "calculator-click.mp3",
      "chime.mp3",
      "wind-ambient.mp3",
    ];
    for (const id of ids) {
      expect(getAsset(id)).toBeDefined();
      expect(getAsset(id)?.kind).toBe("audio");
    }
  });

  it("BRAND_ASSETS is iterable + has at least 10 entries", () => {
    expect(Array.isArray(BRAND_ASSETS) || typeof BRAND_ASSETS[Symbol.iterator] === "function").toBe(
      true,
    );
    expect([...BRAND_ASSETS].length).toBeGreaterThanOrEqual(10);
  });

  it("every entry has a path that begins with /", () => {
    for (const a of BRAND_ASSETS) {
      expect(a.path.startsWith("/")).toBe(true);
    }
  });
});

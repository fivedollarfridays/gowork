/**
 * W5 Driver C — T5.C.3 contract test.
 *
 * Pins the mobile + slow-3G manual test plan.
 */
import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { join } from "node:path";

const PLAN_PATH = join(
  process.cwd(),
  "..",
  "docs",
  "mobile-slow-3g-test-plan.md",
);

describe("docs/mobile-slow-3g-test-plan.md", () => {
  const doc = readFileSync(PLAN_PATH, "utf8");

  it("exists with substantive content (> 1.5 KB)", () => {
    expect(doc.length).toBeGreaterThan(1500);
  });

  it("covers iPhone Safari", () => {
    expect(doc).toMatch(/iPhone/);
    expect(doc).toMatch(/Safari/i);
  });

  it("covers Android Chrome", () => {
    expect(doc).toMatch(/Android/);
    expect(doc).toMatch(/Chrome/);
  });

  it("documents the MobileWallFallback (10 chapter cards)", () => {
    expect(doc).toMatch(/MobileWallFallback/);
    expect(doc).toMatch(/10 (chapter )?cards?|ten chapter/i);
  });

  it("documents the responsive tier check (tablet zoom = 10)", () => {
    expect(doc).toMatch(/tablet|responsive[- ]tier|useResponsiveTier/i);
    expect(doc).toMatch(/zoom/i);
  });

  it("documents slow-3G throttle procedure", () => {
    expect(doc).toMatch(/slow ?3G/i);
    expect(doc).toMatch(/throttle|DevTools/i);
  });

  it("specifies hero text < 3s budget on slow-3G", () => {
    expect(doc).toMatch(/3 ?s|3 seconds|three seconds/);
    expect(doc).toMatch(/hero/i);
  });

  it("documents Mapbox lazy-load behavior", () => {
    expect(doc).toMatch(/lazy[- ]load|defer|after.*scroll/i);
    expect(doc).toMatch(/Mapbox/);
  });

  it("verifies tap targets and scroll behavior on mobile", () => {
    expect(doc).toMatch(/tap target|tap[- ]area/i);
    expect(doc).toMatch(/scroll/i);
  });

  it("contains a checklist (>= 12 checkboxes)", () => {
    const count = (doc.match(/\[ \]/g) ?? []).length;
    expect(count).toBeGreaterThanOrEqual(12);
  });
});

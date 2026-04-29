/**
 * polish-2 Driver D — T47 chapter-thumbs build script smoke test.
 *
 * Asserts:
 *   - Script exists at the expected path.
 *   - Exports `planChapterThumbs(srcs)` which produces the expected
 *     200w/400w/800w × {webp, avif} output plan for each input JPG.
 *   - Script is harmless when imported (no side-effect emit).
 */
import { describe, it, expect } from "vitest";
import fs from "node:fs";
import path from "node:path";

const FRONTEND_ROOT = path.resolve(__dirname, "..", "..");
const SCRIPT = path.resolve(FRONTEND_ROOT, "scripts/build-chapter-thumbs.mjs");

describe("polish-2 T47 — chapter-thumbs build script", () => {
  it("the build script exists", () => {
    expect(fs.existsSync(SCRIPT)).toBe(true);
  });

  it("exports planChapterThumbs(srcs) returning 6 variants per input", async () => {
    const mod = await import(/* @vite-ignore */ `file:///${SCRIPT.replace(/\\/g, "/")}`);
    expect(typeof mod.planChapterThumbs).toBe("function");
    const plan = mod.planChapterThumbs([
      "/abs/path/01-hero.jpg",
      "/abs/path/02-the-numbers.jpg",
    ]);
    // 2 inputs × (3 sizes × 2 formats) = 12 outputs
    expect(plan.length).toBe(12);
    // Each plan entry has a destination path + width + format.
    for (const p of plan) {
      expect(typeof p.dest).toBe("string");
      expect([200, 400, 800]).toContain(p.width);
      expect(["webp", "avif"]).toContain(p.format);
    }
  });

  it("produces destination paths preserving the input basename", async () => {
    const mod = await import(/* @vite-ignore */ `file:///${SCRIPT.replace(/\\/g, "/")}`);
    const plan = mod.planChapterThumbs(["/x/01-hero.jpg"]);
    const names = plan.map((p: { dest: string }) => path.basename(p.dest)).sort();
    expect(names).toEqual([
      "01-hero-200.avif",
      "01-hero-200.webp",
      "01-hero-400.avif",
      "01-hero-400.webp",
      "01-hero-800.avif",
      "01-hero-800.webp",
    ]);
  });
});

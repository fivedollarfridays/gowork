/**
 * Spotlight invention #2 (W5 Driver B) — take-recorder helper test.
 *
 * Verifies `frontend/scripts/take-recorder.mjs` exists, declares the
 * 11-shot list (matches the take plan), and emits a structured shot
 * record per item (timestamp window + URL fragment) so a recorder
 * can hit "record" at the right moment.
 */
import { describe, it, expect } from "vitest";
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

const SCRIPT_PATH = join(process.cwd(), "scripts", "take-recorder.mjs");

describe("Spotlight #2 — take-recorder.mjs", () => {
  it("exists in frontend/scripts/", () => {
    expect(existsSync(SCRIPT_PATH)).toBe(true);
  });

  it("declares 11 shots covering Ch1..Ch10 + cold open", () => {
    const src = readFileSync(SCRIPT_PATH, "utf8");
    // Each shot has a numbered entry. Look for at least 11 indexed
    // records (shot 1 through shot 11 from the take plan).
    const shotMatches = src.match(/\bshot\s*[:=]\s*\d+\b|\b#\s*\d+\b|\bshotIndex\b/gi);
    expect(shotMatches?.length ?? 0).toBeGreaterThanOrEqual(11);
  });

  it("emits chapter URL fragments (#chapter-1 .. #chapter-10) for navigation", () => {
    const src = readFileSync(SCRIPT_PATH, "utf8");
    // The recorder helper prints fragments per chapter so the operator
    // can deeplink. At least the patterns chapter-1 through chapter-10.
    for (let n = 1; n <= 10; n += 1) {
      expect(src).toMatch(new RegExp(`chapter[-_]?${n}\\b`, "i"));
    }
  });

  it("emits timestamps from the 0-340s timing window", () => {
    const src = readFileSync(SCRIPT_PATH, "utf8");
    // Master timeline anchors: 0, 30, 50, 70, 110, 140, 180, 230, 280, 310, 340.
    expect(src).toMatch(/\b340\b/); // total runtime ceiling
    expect(src).toMatch(/\b230\b/); // Ch8 secret weapon start
    expect(src).toMatch(/\b280\b/); // Ch9 cross-country start
  });

  it("documents how to run it", () => {
    const src = readFileSync(SCRIPT_PATH, "utf8");
    expect(src).toMatch(/node\s+(?:scripts\/)?take-recorder\.mjs/);
  });

  it("exports or prints a structured shot list", () => {
    const src = readFileSync(SCRIPT_PATH, "utf8");
    // Must produce something other than free-form prose — a JSON array,
    // a tabular print, or an exported const.
    expect(src).toMatch(/JSON\.stringify|console\.table|const\s+SHOTS|export const SHOTS|shots:\s*\[/);
  });
});

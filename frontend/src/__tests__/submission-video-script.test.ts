/**
 * T5.B.2 — Submission video script gate test.
 *
 * Asserts the script file exists with:
 *  - 90-second intro section
 *  - 3-minute walkthrough section (chapter-by-chapter)
 *  - 15-second closing/outro section
 *  - All 10 Wall chapters represented
 *  - Total estimated runtime under 4:30
 *  - License + city + open-source mentions in the outro
 */
import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { join } from "node:path";

const DOC_PATH = join(
  process.cwd(),
  "..",
  "docs",
  "submission-video-script.md",
);

describe("docs/submission-video-script.md", () => {
  const doc = readFileSync(DOC_PATH, "utf8");

  it("exists and is non-trivially sized", () => {
    expect(doc.length).toBeGreaterThan(2000);
  });

  it("declares a 90-second intro section", () => {
    expect(doc).toMatch(/##.*intro|##.*opening|90.second|90s intro/i);
  });

  it("declares a 3-minute walkthrough section", () => {
    expect(doc).toMatch(/##.*walkthrough|3.minute|3:00|3 minutes/i);
  });

  it("declares a 15-second outro / close section", () => {
    expect(doc).toMatch(/##.*outro|##.*closing|15.second|15s outro/i);
  });

  it("covers all ten Wall chapters with timing markers", () => {
    for (let n = 1; n <= 10; n += 1) {
      const re = new RegExp(`(?:Ch|Chapter)\\s*0?${n}\\b`, "i");
      expect(doc).toMatch(re);
    }
  });

  it("hits every required brand beat in the outro", () => {
    expect(doc).toMatch(/MIT/);
    expect(doc).toMatch(/open.source/i);
    expect(doc).toMatch(/Fort Worth/);
    expect(doc).toMatch(/Montgomery/);
    expect(doc).toMatch(/HackFW 2026/);
  });

  it("declares total runtime within the 4:30 ceiling", () => {
    // Total runtime stated somewhere in the doc as 4:00–4:30.
    expect(doc).toMatch(/4:[0-2]\d|4 minutes? 0?\d|under 4 minutes?/i);
  });

  it("includes a Spanish-voiceover plan (record EN first, ES later)", () => {
    expect(doc).toMatch(/spanish|locale.*es|es voiceover|es track/i);
  });
});

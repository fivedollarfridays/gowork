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

  it("declares an outro / close section (W5-D compressed: outro folded into Ch10)", () => {
    // Driver D compressed runtime to 3:55 to satisfy the
    // visual-rebirth-briefs < 4 min final-cut requirement. The standalone
    // 15s outro folds into Ch10's CTA. Either form is valid: the doc
    // either declares an explicit outro section OR explicitly folds it.
    expect(doc).toMatch(
      /##.*outro|##.*closing|15.second|10.second|outro.*folded|folded into/i,
    );
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

  it("declares total runtime under 4:00 (visual-rebirth-briefs final-cut req)", () => {
    // W5 Driver D — T5.D.6: tightened ceiling from 4:30 to under 4:00 to
    // satisfy `docs/visual-rebirth-briefs.md` ("Final video < 4 min").
    // The script must declare a runtime in the 3:50–3:59 window.
    expect(doc).toMatch(/3:5[0-9]|3 minutes? 5\d|under 4 minutes?/i);
  });

  it("includes a Spanish-voiceover plan (record EN first, ES later)", () => {
    expect(doc).toMatch(/spanish|locale.*es|es voiceover|es track/i);
  });
});

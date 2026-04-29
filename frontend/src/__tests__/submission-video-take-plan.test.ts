/**
 * T5.B.3 — Video take plan gate test.
 *
 * Asserts the take plan exists with:
 *  - 11 numbered shots (per dispatch)
 *  - Multiple-take callouts on the variance-prone shots
 *  - Recording specs (resolution, fps, audio, encoding)
 *  - Ch9 cross-country flight has 5 takes (the highest variance shot)
 *  - Ch8 graph reveal has multiple takes
 */
import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { join } from "node:path";

const DOC_PATH = join(
  process.cwd(),
  "..",
  "docs",
  "submission-video-take-plan.md",
);

describe("docs/submission-video-take-plan.md", () => {
  const doc = readFileSync(DOC_PATH, "utf8");

  it("exists and is non-trivially sized", () => {
    expect(doc.length).toBeGreaterThan(1500);
  });

  it("declares 11 numbered shots from cold open through CTA morph", () => {
    for (let n = 1; n <= 11; n += 1) {
      // Each shot indexed as "1.", "2.", ... "11." somewhere in doc.
      const re = new RegExp(`(?:^|\\n)\\s*${n}\\.\\s+`, "m");
      expect(doc).toMatch(re);
    }
  });

  it("flags Ch9 cross-country flight as 5 takes (highest variance)", () => {
    expect(doc).toMatch(/Ch9[\s\S]*5 takes|5 takes[\s\S]*Ch9|Ch9[\s\S]*MULTIPLE TAKES \(5\)/i);
  });

  it("flags Ch8 graph reveal as multiple takes", () => {
    expect(doc).toMatch(/Ch8[\s\S]*MULTIPLE TAKES|Ch8[\s\S]*\(3\)/i);
  });

  it("declares the recording specs (1920x1080 60fps H.264 MP4)", () => {
    expect(doc).toMatch(/1920\s*[x×]\s*1080/);
    expect(doc).toMatch(/60\s*fps|60fps/i);
    expect(doc).toMatch(/H\.?264/i);
    expect(doc).toMatch(/mp4/i);
    expect(doc).toMatch(/50\s*MB|50 ?MB/i);
  });

  it("names a capture tool (OBS / Loom / QuickTime)", () => {
    expect(doc).toMatch(/OBS|Loom|QuickTime/i);
  });

  it("requires the Ch4 47-form counter to land in a single take", () => {
    expect(doc).toMatch(/47[\s\S]{0,80}counter[\s\S]{0,80}SINGLE TAKE|SINGLE TAKE[\s\S]{0,200}47/i);
  });

  it("calls out the Ch10 View Transitions morph as Chrome-only multi-take", () => {
    // Ch10 must appear with both "MULTIPLE TAKES" and "Chrome" gating;
    // ordering is loose — Chrome qualifier may come before or after.
    expect(doc).toMatch(/Ch10[\s\S]*MULTIPLE TAKES[\s\S]*Chrome|Ch10[\s\S]*Chrome[\s\S]*MULTIPLE TAKES/i);
  });
});

/**
 * T5.B.1 — Submission demo script (Wall walkthrough overlay) gate test.
 *
 * The dispatch requires `docs/submission-demo.md` to be a chapter-locked
 * walkthrough overlay with:
 *  - Per-chapter beats covering Ch1..Ch10
 *  - Locked timing windows that match the dispatch spec
 *  - Backup paths for Mapbox + View Transitions failures
 *  - Pre-demo checklist with Mapbox token / Chrome 135+ / GPU / 4G / ES /
 *    reduced-motion checks
 *
 * If editorial rewrites the chapter copy, these assertions stay stable —
 * the contract here is the structural overlay, not the chapter prose.
 */
import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { join } from "node:path";

const DOC_PATH = join(process.cwd(), "..", "docs", "submission-demo.md");

describe("docs/submission-demo.md (W5 Wall walkthrough overlay)", () => {
  const doc = readFileSync(DOC_PATH, "utf8");

  it("exists and is non-trivially sized", () => {
    expect(doc.length).toBeGreaterThan(2000);
  });

  it("opens with the 30-second hover on Chapter 1", () => {
    // Dispatch: "Opening: 30 seconds hover on Ch1 ('What's standing
    // between you and a job?') — let it breathe."
    expect(doc).toMatch(/Ch1[\s\S]*0[–-]30s/i);
    expect(doc).toMatch(/What's standing between you and a job/);
  });

  it("covers all ten chapters with locked timing windows", () => {
    // Each chapter must appear, and the timing windows from the dispatch
    // must be present verbatim (the seconds are load-bearing).
    const expectedTimings = [
      /Ch1[\s\S]*0[–-]30s/i,
      /Ch2[\s\S]*30[–-]50s/i,
      /Ch3[\s\S]*50[–-]70s/i,
      /Ch4[\s\S]*70[–-]110s/i,
      /Ch5[\s\S]*110[–-]140s/i,
      /Ch6[\s\S]*140[–-]180s/i,
      /Ch7[\s\S]*180[–-]230s/i,
      /Ch8[\s\S]*230[–-]280s/i,
      /Ch9[\s\S]*280[–-]310s/i,
      /Ch10[\s\S]*310[–-]340s/i,
    ];
    for (const re of expectedTimings) {
      expect(doc).toMatch(re);
    }
  });

  it("calls out Ch8 as the secret weapon and Ch9 as cross-country", () => {
    expect(doc).toMatch(/secret weapon/i);
    expect(doc).toMatch(/cross-country|fly to montgomery/i);
  });

  it("includes the 47-form counter anchor for Ch5", () => {
    // The Labyrinth is the visual anchor for Ch5 — counter must be named.
    expect(doc).toMatch(/47[\s\S]{0,40}forms?/i);
  });

  it("declares backup paths for Mapbox + View Transitions failures", () => {
    expect(doc).toMatch(/mapbox/i);
    expect(doc).toMatch(/view transitions?/i);
    expect(doc).toMatch(/firefox/i);
    // There must be a "backup" or "fallback" header so the demo-runner
    // can find it under pressure.
    expect(doc).toMatch(/##.*backup|##.*fallback/i);
  });

  it("includes a pre-demo checklist with all required gates", () => {
    expect(doc).toMatch(/pre-demo checklist|pre.demo checklist/i);
    expect(doc).toMatch(/mapbox token/i);
    expect(doc).toMatch(/chrome 135|chrome\s*1?3?5\+/i);
    expect(doc).toMatch(/GPU|hardware-accelerated/i);
    expect(doc).toMatch(/4g|slow.network/i);
    expect(doc).toMatch(/spanish|locale.*es|es toggle/i);
    expect(doc).toMatch(/reduced.motion|prefers-reduced-motion/i);
  });
});

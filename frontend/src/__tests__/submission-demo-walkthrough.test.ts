/**
 * T5.B.1 — Submission demo script (live judges' demo) gate test.
 *
 * The narrative-reset (sprint/narrative-reset, commit 03dff3c) reverted
 * `docs/submission-demo.md` from the W5-B chapter-locked walkthrough
 * overlay back to a staging-walk script with Beat 1..7 sections (the
 * S13-era live demo flow). The contract here is the structural shape of
 * that script:
 *
 *  - Pitch (verbal opener) with the GoWork thesis
 *  - Beat 1..7 demo flow over the staging environment, with Beat 1
 *    landing on the wall and surfacing Ch1's hero question
 *  - Backup paths section for live-demo recoveries
 *  - Pre-demo checklist (T-30 → T-0) with the stage-warming gates
 *
 * If editorial rewrites the chapter copy, these assertions stay stable —
 * the contract here is the demo-script structure, not the chapter prose.
 */
import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { join } from "node:path";

const DOC_PATH = join(process.cwd(), "..", "docs", "submission-demo.md");

describe("docs/submission-demo.md (live judges' demo script)", () => {
  const doc = readFileSync(DOC_PATH, "utf8");

  it("exists and is non-trivially sized", () => {
    expect(doc.length).toBeGreaterThan(2000);
  });

  it("opens Beat 1 by surfacing Ch1's hero question on the wall", () => {
    // Narrative-reset Beat 1: "Land on the wall. Let Ch1's hero question
    // breathe — 'What's standing between you and a job?' — over the
    // cinematic Mapbox view of Fort Worth." The 0-30s timing window from
    // the W5-B overlay was dropped when the doc reverted to the
    // staging-walk Beat 1..7 script; we now assert the substantive Beat
    // 1 content instead.
    expect(doc).toMatch(/Beat 1\b/i);
    expect(doc).toMatch(/Ch1/i);
    // Hero question can wrap across lines in the markdown body — use
    // `\s+` between words so a soft-wrapped quote still matches.
    expect(doc).toMatch(/What's\s+standing\s+between\s+you\s+and\s+a\s+job/);
  });

  it("covers a Beat 1..7 demo flow with timing budgets", () => {
    // Each Beat must appear by name, and the per-beat seconds budget
    // (e.g. "60s" / "45s" / "30s") must be present in the script — the
    // operator times against these. The narrative-reset doc uses
    // Beat 1..7 in place of the W5-B Ch1..Ch10 overlay structure.
    const expectedBeats = [
      /Beat 1\b[\s\S]*60s/i,
      /Beat 2\b[\s\S]*60s/i,
      /Beat 3\b[\s\S]*45s/i,
      /Beat 4\b[\s\S]*45s/i,
      /Beat 5\b[\s\S]*30s/i,
      /Beat 6\b[\s\S]*45s/i,
      /Beat 7\b[\s\S]*30s/i,
    ];
    for (const re of expectedBeats) {
      expect(doc).toMatch(re);
    }
  });

  it("calls out the compliance gate and the case manager view", () => {
    // Differentiator beats from the staging-walk script: Beat 5 is the
    // compliance gate (the production-grade differentiator a city
    // procurement officer asks about) and Beat 6 is the case manager
    // tandem (advisor token + same-data-model on both sides).
    expect(doc).toMatch(/compliance gate/i);
    expect(doc).toMatch(/case manager/i);
  });

  it("includes the differentiator pitch (barrier-removal, not job-search)", () => {
    // The doc's Pitch section pins the differentiator: "we are not a
    // job-search tool. We are a barrier-removal tool with a job-search
    // tool inside it." That phrase is load-bearing — it carries the
    // entire opening verbal pitch.
    expect(doc).toMatch(/barrier[- ]removal/i);
    expect(doc).toMatch(/job[- ]search/i);
  });

  it("declares backup paths for live-demo recoveries", () => {
    // Narrative-reset backup paths cover Fly.io cold-starts, demo data
    // drift, resume-gen failures, drag failures, advisor-token rejects,
    // and a fallback to slides + screenshots. The "backup" section
    // header is load-bearing — the operator scans for it under pressure.
    expect(doc).toMatch(/##.*backup|##.*fallback/i);
    expect(doc).toMatch(/cold[- ]start/i);
    expect(doc).toMatch(/staging|fly\.io/i);
  });

  it("includes a pre-demo checklist with the staging-warm gates", () => {
    // Narrative-reset pre-demo checklist drops the Mapbox-token / Chrome
    // 135 / GPU / 4G / ES / reduced-motion gates from the W5-B overlay
    // and uses the staging-walk gates instead: T-30..T-0 stage-warming
    // (wake machines, verify demo data, smoke check, pre-load tabs,
    // re-warm at T-2).
    expect(doc).toMatch(/pre-demo checklist|pre.demo checklist/i);
    expect(doc).toMatch(/T-30|T\s*minus\s*30/i);
    expect(doc).toMatch(/staging|fly\.io|fly ssh/i);
    expect(doc).toMatch(/smoke (check|script)|staging-smoke/i);
    expect(doc).toMatch(/pre-?load|preload/i);
  });
});

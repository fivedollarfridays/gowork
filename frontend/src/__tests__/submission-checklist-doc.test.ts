/**
 * W5 Driver C — T5.C.5 contract test.
 *
 * The submission checklist is the ONE artifact that prevents missing the
 * May 2 cutoff. Pin its required sections so a quiet edit cannot delete
 * a step.
 */
import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { join } from "node:path";

const CHECKLIST_PATH = join(
  process.cwd(),
  "..",
  "docs",
  "submission-checklist.md",
);

describe("docs/submission-checklist.md — HackFW T-1 hour checklist", () => {
  const doc = readFileSync(CHECKLIST_PATH, "utf8");

  it("exists with substantive content (> 2 KB)", () => {
    expect(doc.length).toBeGreaterThan(2000);
  });

  it("declares the May 2, 2026 2:00 PM CDT deadline", () => {
    expect(doc).toMatch(/May 2,? 2026/);
    expect(doc).toMatch(/2:00 ?PM CDT|14:00 ?CDT/i);
  });

  it("contains all 5 phase headings (T-2h through T+15min)", () => {
    expect(doc).toMatch(/T-2 ?hours?/i);
    expect(doc).toMatch(/T-1 ?hour/i);
    expect(doc).toMatch(/T-30 ?min/i);
    expect(doc).toMatch(/T-15 ?min/i);
    expect(doc).toMatch(/T\+15 ?min/i);
  });

  it("references the Lighthouse 0.90 floor verification", () => {
    expect(doc).toMatch(/Lighthouse/);
    expect(doc).toMatch(/0\.9|≥ ?0\.90|≥ ?90|>= ?0\.9/);
  });

  it("requires Mapbox token verification on production", () => {
    expect(doc).toMatch(/Mapbox/);
    expect(doc).toMatch(/production|prod/i);
  });

  it("requires the OG card visual confirmation", () => {
    expect(doc).toMatch(/api\/og\/1|OG card/i);
  });

  it("requires the mobile fallback verification", () => {
    expect(doc).toMatch(/Mobile|iPhone|Android|fallback/i);
  });

  it("requires the Spanish toggle verification", () => {
    expect(doc).toMatch(/Spanish|ES toggle|español/i);
  });

  it("requires the reduced-motion verification", () => {
    expect(doc).toMatch(/[Rr]educed[- ]motion/);
  });

  it("requires the skip-to-content link verification", () => {
    expect(doc).toMatch(/[Ss]kip[- ]to[- ]content|skip link/i);
  });

  it("references the git tag step at T+15 min", () => {
    expect(doc).toMatch(/v0\.1\.0[- ]hackfw[- ]submission/);
    expect(doc).toMatch(/git tag/i);
  });

  it("references the Devpost form fields and the production URL", () => {
    expect(doc).toMatch(/Devpost/);
    expect(doc).toMatch(/Try it out|production URL|live URL/i);
  });

  it("references the video upload constraints (size and runtime)", () => {
    expect(doc).toMatch(/50 ?MB/);
    expect(doc).toMatch(/4:30|3:30|video/i);
  });

  it("counts at least 25 checkbox items (full checklist coverage)", () => {
    const checkboxCount = (doc.match(/\[ \]/g) ?? []).length;
    expect(checkboxCount).toBeGreaterThanOrEqual(25);
  });

  it("declares the buffer rule (target submit before deadline)", () => {
    // W5 backlog locks 9 AM CDT submit (5h buffer). Checklist must echo.
    expect(doc).toMatch(/buffer|9:00 ?AM|9 ?AM/i);
  });
});

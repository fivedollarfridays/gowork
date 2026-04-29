/**
 * W5 Driver C — T5.C.2 contract test.
 *
 * Pins the cross-browser test plan as a manual-QA checklist so a quiet
 * deletion (or a missing browser entry) is caught at vitest.
 */
import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { join } from "node:path";

const PLAN_PATH = join(
  process.cwd(),
  "..",
  "docs",
  "cross-browser-test-plan.md",
);

describe("docs/cross-browser-test-plan.md", () => {
  const doc = readFileSync(PLAN_PATH, "utf8");

  it("exists with substantive content (> 2 KB)", () => {
    expect(doc.length).toBeGreaterThan(2000);
  });

  it("covers all 4 target browsers", () => {
    expect(doc).toMatch(/Chrome/);
    expect(doc).toMatch(/Safari/);
    expect(doc).toMatch(/Firefox/);
    expect(doc).toMatch(/Edge/);
  });

  it("documents View Transitions Safari/Firefox fallback expectations", () => {
    expect(doc).toMatch(/View Transitions?/i);
    expect(doc).toMatch(/fallback|graceful|standard nav/i);
  });

  it("lists the canonical pages to walk per browser", () => {
    expect(doc).toMatch(/\//);
    expect(doc).toMatch(/\/assess/);
    expect(doc).toMatch(/\/plan/);
    expect(doc).toMatch(/\/api\/og\//);
  });

  it("specifies functional tests (Ch1->Ch10 scroll, slider, fly-to, CTA)", () => {
    expect(doc).toMatch(/Ch1.*Ch10|chapter 1.*chapter 10|scroll Ch/i);
    expect(doc).toMatch(/wage slider|Ch6/i);
    expect(doc).toMatch(/Montgomery|fly-to|Ch9/i);
    expect(doc).toMatch(/CTA|Ch10/i);
  });

  it("specifies a11y tests (keyboard tab + screen reader)", () => {
    expect(doc).toMatch(/keyboard|Tab/i);
    expect(doc).toMatch(/screen reader|VoiceOver|NVDA/i);
  });

  it("specifies visual regression / screenshot diff", () => {
    expect(doc).toMatch(/screenshot|visual regression|baseline/i);
  });

  it("contains a checklist (>= 30 checkboxes covering 4 browsers)", () => {
    const count = (doc.match(/\[ \]/g) ?? []).length;
    expect(count).toBeGreaterThanOrEqual(30);
  });

  it("explicitly states this is a MANUAL QA plan (no automation)", () => {
    expect(doc).toMatch(/manual/i);
  });

  it("specifies minimum browser versions (Chrome 135+, Safari 17+, etc.)", () => {
    expect(doc).toMatch(/Chrome\s+\d+\+|Chrome\s+\d{2,}/);
    expect(doc).toMatch(/Safari\s+\d+\+/);
    expect(doc).toMatch(/Firefox\s+\d+\+/);
  });
});

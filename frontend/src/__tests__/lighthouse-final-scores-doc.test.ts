/**
 * W5 Driver C — T5.C.1 contract test.
 *
 * Pin the structure of `docs/lighthouse-final-scores.md` so the document
 * always carries the four scores, the timestamp, and (if measurement
 * fails locally) the exact run path Shawn or CI must execute.
 */
import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { join } from "node:path";

const DOC_PATH = join(
  process.cwd(),
  "..",
  "docs",
  "lighthouse-final-scores.md",
);

describe("docs/lighthouse-final-scores.md", () => {
  const doc = readFileSync(DOC_PATH, "utf8");

  it("exists with substantive content (> 1.5 KB)", () => {
    expect(doc.length).toBeGreaterThan(1500);
  });

  it("documents all 4 categories with their floors", () => {
    expect(doc).toMatch(/[Pp]erformance/);
    expect(doc).toMatch(/[Aa]ccessibility/);
    expect(doc).toMatch(/[Bb]est[- ][Pp]ractices/);
    expect(doc).toMatch(/SEO|Seo/);
    // 0.90 hard gate per W5 Driver C brief
    expect(doc).toMatch(/0\.90|≥ ?0\.90|≥ ?90/);
  });

  it("documents the local lhci run path (build + lhci)", () => {
    expect(doc).toMatch(/npm run build/);
    expect(doc).toMatch(/npm run lhci|lhci autorun/);
  });

  it("specifies a measurement timestamp field", () => {
    expect(doc).toMatch(/[Tt]imestamp|[Mm]easured at|[Mm]easured on/);
  });

  it("documents the descope priority order if a category is below floor", () => {
    expect(doc).toMatch(/audio/i);
    expect(doc).toMatch(/temperature/i);
    expect(doc).toMatch(/3D|three[- ]?d/i);
    expect(doc).toMatch(/View Transitions?/i);
  });

  it("documents that descope must precede lowering the floor", () => {
    // Brief: "DO NOT lower the floor as a shortcut."
    expect(doc).toMatch(/DO NOT lower|do not lower|never lower|not.*lower/i);
  });

  it("documents an honest-uncertainty section if local measurement failed", () => {
    expect(doc).toMatch(/[Hh]onest [Uu]ncertainty|[Uu]ncertainty/);
  });

  it("references the lighthouserc.json config", () => {
    expect(doc).toMatch(/lighthouserc\.json/);
  });
});

/**
 * Spanish translation review checklist (Wave 2 cross-driver integration).
 *
 * Verifies the doc exists, lists the four most-loaded strings, and provides
 * reviewer prompts. The doc is the gate for the W4 Spanish-parity pass.
 */
import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { join } from "node:path";

const DOC_PATH = join(
  process.cwd(),
  "..",
  "docs",
  "spanish-translation-review.md",
);

describe("docs/spanish-translation-review.md", () => {
  const doc = readFileSync(DOC_PATH, "utf8");

  it("exists and is non-empty", () => {
    expect(doc.length).toBeGreaterThan(500);
  });

  it("lists the 4 most-loaded strings as numbered sections", () => {
    expect(doc).toMatch(/String 1 — 404 wall metaphor/);
    expect(doc).toMatch(/String 2 — 500 calibrating motif/);
    expect(doc).toMatch(/String 3 — Footer brand label/);
    expect(doc).toMatch(/String 4 — Header brand/);
  });

  it("includes EN + ES side-by-side for each string", () => {
    expect(doc).toMatch(/\*\*English:\*\*/g);
    expect(doc).toMatch(/\*\*Spanish:\*\*/);
    // 404 specifically — this is the wall-metaphor sentinel.
    expect(doc).toMatch(/path to this URL/);
    expect(doc).toMatch(/través del muro/);
  });

  it("provides reviewer prompts as actionable checklists", () => {
    const checkboxCount = (doc.match(/- \[ \]/g) ?? []).length;
    expect(checkboxCount).toBeGreaterThanOrEqual(8);
  });

  it("declares a sign-off section so the reviewer can mark approval", () => {
    expect(doc).toMatch(/Sign-off/);
    expect(doc).toMatch(/Reviewer name/);
    expect(doc).toMatch(/Approved/);
  });
});

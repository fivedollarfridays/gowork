/**
 * Spotlight invention 5 — landmark map (lib/wall/landmarks.ts).
 *
 * SkipToContent currently jumps to a single `#main`. The W2/W3 wall has
 * multiple landmarks: header, main, footer, chapter-list, language-toggle.
 * A keyboard user pressing Tab once should be able to choose where to
 * land. This module declares the canonical anchor map; SkipToContent
 * v2 (W4) renders a menu sourced from it.
 */
import { describe, it, expect } from "vitest";
import { LANDMARKS, getLandmark } from "../landmarks";

describe("landmark map", () => {
  it("declares the canonical four landmarks", () => {
    const ids = LANDMARKS.map((l) => l.id);
    expect(ids).toEqual(
      expect.arrayContaining(["main", "header", "footer", "chapters"]),
    );
  });

  it("each landmark has an id, anchor, and i18n labelKey", () => {
    for (const lm of LANDMARKS) {
      expect(lm.id).toBeTruthy();
      expect(lm.anchor.startsWith("#")).toBe(true);
      expect(lm.labelKey).toMatch(/a11y\.landmarks\./);
    }
  });

  it("getLandmark('main') returns the main landmark", () => {
    expect(getLandmark("main")?.anchor).toBe("#main");
  });
});

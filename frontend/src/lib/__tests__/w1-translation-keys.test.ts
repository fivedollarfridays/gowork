/**
 * W1 Driver C — translation key contract.
 *
 * Asserts that every key the W1 lane components consume exists in BOTH
 * `en.json` and `es.json`. The Spanish copy uses the formal-but-warm
 * voice already established in the catalog. Spanish strings under active
 * cultural review are flagged with the `[ES-pending-review]` suffix at
 * commit time and surfaced in the delivery message.
 *
 * Keys covered:
 *   - edge.404.{title,body,cta}, edge.500.{title,body,cta}
 *   - edge.empty.{title,body}, edge.loading.label
 *   - wall.titleSequence.{presenter,title,subtitle}
 *   - header.brand.label, header.muteToggle.aria,
 *     header.languageToggle.aria, header.github.aria,
 *     header.chapterCounter.aria
 *   - footer.brand.label, footer.github, footer.license,
 *     footer.lastCalibration  (new keys, additive — privacy/terms preserved)
 *   - a11y.skipToContent
 */
import { describe, it, expect } from "vitest";
import en from "../translations/en.json";
import es from "../translations/es.json";

const REQUIRED_KEYS = [
  // Edge states (404 / 500 / empty / loading)
  ["edge", "404", "title"],
  ["edge", "404", "body"],
  ["edge", "404", "cta"],
  ["edge", "500", "title"],
  ["edge", "500", "body"],
  ["edge", "500", "cta"],
  ["edge", "empty", "title"],
  ["edge", "empty", "body"],
  ["edge", "loading", "label"],
  // Wall — title sequence
  ["wall", "titleSequence", "presenter"],
  ["wall", "titleSequence", "title"],
  ["wall", "titleSequence", "subtitle"],
  // Header
  ["header", "brand", "label"],
  ["header", "muteToggle", "aria"],
  ["header", "languageToggle", "aria"],
  ["header", "github", "aria"],
  ["header", "chapterCounter", "aria"],
  // Footer (additive — preserves the existing footer.* test contract)
  ["footer", "brand", "label"],
  ["footer", "github"],
  ["footer", "license"],
  ["footer", "lastCalibration"],
  // A11y
  ["a11y", "skipToContent"],
] as const;

function read(catalog: unknown, path: readonly string[]): unknown {
  let node: unknown = catalog;
  for (const segment of path) {
    if (node == null || typeof node !== "object") return undefined;
    node = (node as Record<string, unknown>)[segment];
  }
  return node;
}

describe("W1 driver-C translation keys", () => {
  for (const path of REQUIRED_KEYS) {
    const dotted = path.join(".");
    it(`en.${dotted} is a non-empty string`, () => {
      const value = read(en, path);
      expect(typeof value).toBe("string");
      expect((value as string).length).toBeGreaterThan(0);
    });

    it(`es.${dotted} is a non-empty string`, () => {
      const value = read(es, path);
      expect(typeof value).toBe("string");
      expect((value as string).length).toBeGreaterThan(0);
    });
  }

  it("preserves the legacy footer.entity / footer.tagline / footer.privacy / footer.terms / footer.navLabel keys", () => {
    for (const k of ["entity", "tagline", "navLabel", "privacy", "terms"]) {
      expect(typeof (en as { footer: Record<string, unknown> }).footer[k]).toBe(
        "string",
      );
      expect(typeof (es as { footer: Record<string, unknown> }).footer[k]).toBe(
        "string",
      );
    }
  });

  it("does not contain stray MontGoWork wordmark in W1 user-facing copy", () => {
    const probe = (cat: unknown, paths: readonly (readonly string[])[]) => {
      for (const p of paths) {
        const v = read(cat, p);
        if (typeof v === "string") {
          expect(v).not.toMatch(/MontGoWork/);
        }
      }
    };
    const w1Paths: readonly (readonly string[])[] = [
      ["edge", "404", "title"],
      ["edge", "404", "body"],
      ["edge", "500", "title"],
      ["edge", "500", "body"],
      ["wall", "titleSequence", "presenter"],
      ["wall", "titleSequence", "title"],
      ["wall", "titleSequence", "subtitle"],
      ["header", "brand", "label"],
      ["footer", "brand", "label"],
    ];
    probe(en, w1Paths);
    probe(es, w1Paths);
  });
});

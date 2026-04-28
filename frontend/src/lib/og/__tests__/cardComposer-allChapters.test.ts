/**
 * Per-chapter resolveChapterMeta detail tests.
 *
 * One test per chapter (1..10) per locale (en, es) asserting:
 *   - title is present and non-empty
 *   - hero copy is present and non-empty
 *   - accent token is one of the W4 5-token set
 *
 * If a future chapter adds editorial copy via a non-`hero` key, the
 * fallback chain (hero → heroQuestion → lede → editorial → body) ensures
 * something prints. This test pins the contract.
 */

import { describe, it, expect } from "vitest";
import {
  resolveChapterMeta,
  composeChapterCard,
  type ChapterNumber,
} from "../cardComposer";

const ALLOWED_ACCENTS = ["amber", "cyan", "blue", "rose", "indigo"];

const ALL_CHAPTERS: ChapterNumber[] = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];

describe("resolveChapterMeta — English copy is editorial-grade", () => {
  for (const n of ALL_CHAPTERS) {
    it(`chapter ${n} has a non-empty title and hero in English`, () => {
      const m = resolveChapterMeta(n, "en");
      expect(m.title.length).toBeGreaterThan(2);
      expect(m.hero.length).toBeGreaterThan(2);
      expect(ALLOWED_ACCENTS).toContain(m.accent);
    });
  }
});

describe("resolveChapterMeta — Spanish copy is editorial-grade", () => {
  for (const n of ALL_CHAPTERS) {
    it(`chapter ${n} has a non-empty title and hero in Spanish`, () => {
      const m = resolveChapterMeta(n, "es");
      expect(m.title.length).toBeGreaterThan(2);
      expect(m.hero.length).toBeGreaterThan(2);
    });
  }
});

describe("resolveChapterMeta — accent token coherence", () => {
  it("Ch1 uses 'amber' (Continental dawn)", () => {
    expect(resolveChapterMeta(1, "en").accent).toBe("amber");
  });
  it("Ch2 uses 'cyan' (Trinity Metro)", () => {
    expect(resolveChapterMeta(2, "en").accent).toBe("cyan");
  });
  it("Ch3 uses 'blue' (community)", () => {
    expect(resolveChapterMeta(3, "en").accent).toBe("blue");
  });
  it("Ch4 uses 'rose' (the wall flush)", () => {
    expect(resolveChapterMeta(4, "en").accent).toBe("rose");
  });
  it("Ch5 uses 'indigo' (labyrinth depth)", () => {
    expect(resolveChapterMeta(5, "en").accent).toBe("indigo");
  });
  it("Ch10 uses 'rose' (the invitation)", () => {
    expect(resolveChapterMeta(10, "en").accent).toBe("rose");
  });
});

describe("composeChapterCard — accentHex is a valid sRGB", () => {
  for (const n of ALL_CHAPTERS) {
    it(`chapter ${n} returns a 7-char #RRGGBB hex`, () => {
      const m = resolveChapterMeta(n, "en");
      expect(m.accentHex).toMatch(/^#[0-9A-Fa-f]{6}$/);
    });
  }
});

describe("composeChapterCard — meta+tree consistency", () => {
  for (const n of ALL_CHAPTERS) {
    it(`chapter ${n} card.tree carries the same accent visually`, () => {
      const card = composeChapterCard(n, "en");
      // Walk the tree's children — at least one element should reference
      // the accent hex in inline styles.
      const json = JSON.stringify(card.tree);
      expect(json).toContain(card.meta.accentHex);
    });
  }
});

describe("composeChapterCard — title + hero are in the rendered tree", () => {
  for (const n of ALL_CHAPTERS) {
    it(`chapter ${n} (en): hero copy appears in tree text content`, () => {
      const card = composeChapterCard(n, "en");
      const json = JSON.stringify(card.tree);
      expect(json).toContain(card.meta.hero);
    });
    it(`chapter ${n} (es): hero copy appears in tree text content`, () => {
      const card = composeChapterCard(n, "es");
      const json = JSON.stringify(card.tree);
      expect(json).toContain(card.meta.hero);
    });
  }
});

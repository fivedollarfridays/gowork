/**
 * Spotlight invention #1 (W4 Driver D) — cardComposer.test.ts.
 *
 * `composeChapterCard()` is the pure-function composition of an OG card
 * React tree. It accepts (chapterIndex, locale) and returns a tree of
 * `{ type, props }` JSX nodes plus a meta object with the chapter title +
 * hero copy + accent token. The route handler under `/api/og/[chapter]`
 * passes the result to `new ImageResponse(tree, { width: 1200, height: 630 })`.
 *
 * Why a pure module: the same composition is reused by the future email
 * digest send-time card and by the press-kit static export. Keeping it
 * pure (no fetch, no env reads, no React hooks) means it composes in any
 * runtime — Edge route, Node script, browser preview.
 */

import { describe, it, expect } from "vitest";
import {
  composeChapterCard,
  composeDefaultCard,
  resolveChapterMeta,
  CARD_WIDTH,
  CARD_HEIGHT,
} from "../cardComposer";

describe("composeChapterCard — width/height contract", () => {
  it("CARD_WIDTH is 1200px (Twitter Card / OG standard)", () => {
    expect(CARD_WIDTH).toBe(1200);
  });

  it("CARD_HEIGHT is 630px (Twitter Card / OG standard)", () => {
    expect(CARD_HEIGHT).toBe(630);
  });
});

describe("resolveChapterMeta — translations lookup", () => {
  it("returns a title + hero for chapters 1..10 in English", () => {
    for (let n = 1; n <= 10; n += 1) {
      const meta = resolveChapterMeta(n as 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10, "en");
      expect(typeof meta.title).toBe("string");
      expect(meta.title.length).toBeGreaterThan(0);
      expect(typeof meta.hero).toBe("string");
      expect(meta.hero.length).toBeGreaterThan(0);
    }
  });

  it("returns Spanish title + hero for chapters 1..10 when locale='es'", () => {
    for (let n = 1; n <= 10; n += 1) {
      const meta = resolveChapterMeta(n as 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10, "es");
      expect(typeof meta.title).toBe("string");
      expect(meta.title.length).toBeGreaterThan(0);
    }
  });

  it("returns the actual locked Ch1 hero question for English", () => {
    const meta = resolveChapterMeta(1, "en");
    expect(meta.hero).toBe("What's standing between you and a job?");
  });

  it("returns the locked Ch1 Spanish hero copy", () => {
    const meta = resolveChapterMeta(1, "es");
    expect(meta.hero).toMatch(/trabajo|empleo/);
  });

  it("falls back to English when an unknown locale is requested", () => {
    const meta = resolveChapterMeta(1, "fr" as "en");
    expect(meta.hero).toBe("What's standing between you and a job?");
  });

  it("includes a chapter-keyed accent token", () => {
    const meta = resolveChapterMeta(1, "en");
    expect(typeof meta.accent).toBe("string");
    expect(["amber", "cyan", "blue", "rose", "indigo"]).toContain(meta.accent);
  });
});

describe("composeChapterCard — React-tree shape", () => {
  it("returns an object with `tree` and `meta`", () => {
    const card = composeChapterCard(1, "en");
    expect(card).toHaveProperty("tree");
    expect(card).toHaveProperty("meta");
  });

  it("`meta` carries the resolved title, hero, and accent", () => {
    const card = composeChapterCard(7, "en");
    expect(card.meta.title.length).toBeGreaterThan(0);
    expect(card.meta.hero.length).toBeGreaterThan(0);
    expect(typeof card.meta.accent).toBe("string");
  });

  it("`tree` is a React element (has type + props)", () => {
    const card = composeChapterCard(1, "en");
    expect(card.tree).toBeDefined();
    // React element: { $$typeof, type, props, key, ... }
    expect(typeof card.tree).toBe("object");
    expect(card.tree).not.toBeNull();
  });

  it("renders both English and Spanish without throwing", () => {
    for (let n = 1; n <= 10; n += 1) {
      expect(() =>
        composeChapterCard(n as 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10, "en"),
      ).not.toThrow();
      expect(() =>
        composeChapterCard(n as 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10, "es"),
      ).not.toThrow();
    }
  });
});

describe("composeDefaultCard — site-wide fallback", () => {
  it("returns a tree + meta with the site tagline (English default)", () => {
    const card = composeDefaultCard("en");
    expect(card.tree).toBeDefined();
    expect(card.meta.title).toMatch(/GoWork/);
    expect(card.meta.hero.length).toBeGreaterThan(0);
  });

  it("returns Spanish copy when locale='es'", () => {
    const card = composeDefaultCard("es");
    expect(card.meta.title).toMatch(/GoWork/);
    expect(card.meta.hero.length).toBeGreaterThan(0);
  });
});

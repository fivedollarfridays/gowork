/**
 * W4 Driver C Spotlight #1 — keyboardNavigationContract tests.
 *
 * The contract centralizes the expected Tab order on `/` so the Playwright
 * keyboard sweep AND any future a11y audit reads from the same source.
 * Without it, every audit re-discovers the order, drifts, and regressions
 * sneak in ("oh, the language toggle is now BEFORE the brand mark — fine?").
 *
 * These tests pin the source-of-truth contract. The Playwright e2e
 * `keyboard-sweep.spec.ts` is the live verification.
 */
import { describe, it, expect } from "vitest";
import {
  HOMEPAGE_TAB_ORDER,
  isFocusableSelector,
  expectedTabOrderLength,
  selectorAt,
  type FocusableEntry,
} from "../keyboardNavigationContract";

describe("keyboardNavigationContract — HOMEPAGE_TAB_ORDER", () => {
  it("is a non-empty array", () => {
    expect(Array.isArray(HOMEPAGE_TAB_ORDER)).toBe(true);
    expect(HOMEPAGE_TAB_ORDER.length).toBeGreaterThan(0);
  });

  it("first entry is the skip-to-content link (must be first focusable)", () => {
    const first = HOMEPAGE_TAB_ORDER[0];
    expect(first.id).toBe("skip-to-content");
    expect(first.selector).toContain("skip-to-content");
  });

  it("every entry has a stable id, a CSS selector, and a human label", () => {
    for (const entry of HOMEPAGE_TAB_ORDER) {
      expect(typeof entry.id).toBe("string");
      expect(entry.id.length).toBeGreaterThan(0);
      expect(typeof entry.selector).toBe("string");
      expect(entry.selector.length).toBeGreaterThan(0);
      expect(typeof entry.label).toBe("string");
      expect(entry.label.length).toBeGreaterThan(0);
    }
  });

  it("ids are unique across the whole order (no duplicates)", () => {
    const ids = HOMEPAGE_TAB_ORDER.map((e) => e.id);
    const unique = new Set(ids);
    expect(unique.size).toBe(ids.length);
  });

  it("includes brand mark, language toggle, and mute toggle (header chrome)", () => {
    const ids = HOMEPAGE_TAB_ORDER.map((e) => e.id);
    expect(ids).toContain("brand-mark");
    expect(ids).toContain("language-toggle");
    expect(ids).toContain("mute-toggle");
  });
});

describe("keyboardNavigationContract — selectorAt()", () => {
  it("returns the entry at the given index", () => {
    const entry = selectorAt(0);
    expect(entry).toEqual(HOMEPAGE_TAB_ORDER[0]);
  });

  it("returns undefined out of range", () => {
    expect(selectorAt(99999)).toBeUndefined();
    expect(selectorAt(-1)).toBeUndefined();
  });
});

describe("keyboardNavigationContract — expectedTabOrderLength()", () => {
  it("matches HOMEPAGE_TAB_ORDER.length", () => {
    expect(expectedTabOrderLength()).toBe(HOMEPAGE_TAB_ORDER.length);
  });
});

describe("keyboardNavigationContract — isFocusableSelector()", () => {
  it("accepts a CSS selector with class or attribute (truthy guard)", () => {
    expect(isFocusableSelector(".skip-to-content")).toBe(true);
    expect(isFocusableSelector("[data-testid='nav-link']")).toBe(true);
    expect(isFocusableSelector("button")).toBe(true);
  });

  it("rejects empty selectors", () => {
    expect(isFocusableSelector("")).toBe(false);
    expect(isFocusableSelector("   ")).toBe(false);
  });
});

describe("keyboardNavigationContract — FocusableEntry shape", () => {
  it("is a typed structural contract (compile-time narrative)", () => {
    const entry: FocusableEntry = {
      id: "x",
      selector: ".x",
      label: "X",
    };
    expect(entry.id).toBe("x");
  });
});

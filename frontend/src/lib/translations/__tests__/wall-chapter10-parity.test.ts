/**
 * W3 Driver C — T3.22 — Chapter 10 translation parity (EN/ES).
 *
 * Mirrors the W2 wall-namespace-parity contract. Every wall.chapter10.*
 * key declared in EN must appear in ES (and vice-versa), and the
 * required keys for Driver C's Chapter10FindYourPath component must be
 * resolvable in both locales.
 *
 * If souji catches `[ES-pending-review]` markers in any chapter10 ES
 * value, that's expected during W3 — the marker is the audit signal,
 * NOT a parity failure. The marker stays until W4's translation review.
 */
import { describe, expect, it } from "vitest";
import en from "../en.json";
import es from "../es.json";

type Dict = Record<string, unknown>;

function getNested(dict: Dict, path: string): unknown {
  const parts = path.split(".");
  let node: unknown = dict;
  for (const p of parts) {
    if (node == null || typeof node !== "object") return undefined;
    node = (node as Record<string, unknown>)[p];
  }
  return node;
}

/**
 * Required chapter 10 keys consumed by Chapter10FindYourPath.tsx.
 *
 * Native-fluent ES required for ALL of these. Where the translator was
 * unsure, the value carries an inline `[ES-pending-review]` marker.
 */
const CH10_REQUIRED_KEYS = [
  "wall.chapter10.title",
  "wall.chapter10.hero",
  "wall.chapter10.subhero",
  "wall.chapter10.body",
  "wall.chapter10.aria",
  "wall.chapter10.ctaPrimary",
  "wall.chapter10.ctaSecondary",
  "wall.chapter10.githubLinkLabel",
  "wall.chapter10.footerBrand",
];

describe("W3 — wall.chapter10.* parity (EN/ES)", () => {
  it.each(CH10_REQUIRED_KEYS)("EN has key %s as a string", (key) => {
    expect(getNested(en, key), `Missing key in en.json: ${key}`).toBeTypeOf(
      "string",
    );
  });

  it.each(CH10_REQUIRED_KEYS)("ES has key %s as a string", (key) => {
    expect(getNested(es, key), `Missing key in es.json: ${key}`).toBeTypeOf(
      "string",
    );
  });

  it("EN and ES wall.chapter10 expose the SAME key shape", () => {
    const enCh10 = getNested(en, "wall.chapter10");
    const esCh10 = getNested(es, "wall.chapter10");
    expect(enCh10).toBeTruthy();
    expect(esCh10).toBeTruthy();
    const enKeys = Object.keys(enCh10 as Dict).sort();
    const esKeys = Object.keys(esCh10 as Dict).sort();
    expect(esKeys).toEqual(enKeys);
  });

  it("ES values are non-empty (no zero-length placeholder strings)", () => {
    for (const key of CH10_REQUIRED_KEYS) {
      const value = getNested(es, key);
      expect(typeof value).toBe("string");
      expect((value as string).trim().length).toBeGreaterThan(0);
    }
  });
});

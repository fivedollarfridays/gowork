/**
 * Driver D Wave 3 — translation namespace consolidation parity test.
 *
 * Three contracts:
 *   1. EVERY chapter1..5 i18n key under `wall.chapter0N.*` exists in BOTH
 *      en.json AND es.json.
 *   2. There is NO `wall.ch1`, `wall.ch2`, or `wall.ch3` namespace
 *      remaining (Driver B's pre-consolidation namespace).
 *   3. The chapters Driver B's components use (title/body/hero/subhero/aria)
 *      all resolve under the canonical `wall.chapter0N.*` namespace.
 */
import { describe, expect, it } from "vitest";
import en from "../en.json";
import es from "../es.json";

type TranslationDict = Record<string, unknown>;

function getNested(dict: TranslationDict, path: string): unknown {
  const parts = path.split(".");
  let node: unknown = dict;
  for (const p of parts) {
    if (node == null || typeof node !== "object") return undefined;
    node = (node as Record<string, unknown>)[p];
  }
  return node;
}

const W2_CANONICAL_KEYS = [
  // Chapter 1
  "wall.chapter01.heroQuestion",
  "wall.chapter01.title",
  "wall.chapter01.hero",
  "wall.chapter01.subhero",
  "wall.chapter01.aria",
  // Chapter 2
  "wall.chapter02.title",
  "wall.chapter02.body",
  "wall.chapter02.aria",
  // Chapter 3
  "wall.chapter03.title",
  "wall.chapter03.body",
  "wall.chapter03.aria",
  // Chapter 4 (parent + sub-chapters preserved as-is from Driver C)
  "wall.chapter04.title",
  "wall.chapter04.aria",
  "wall.chapter04a.title",
  "wall.chapter04b.title",
  "wall.chapter04c.title",
  "wall.chapter04d.title",
  // Chapter 5
  "wall.chapter05.title",
  "wall.chapter05.editorial",
];

describe("Wave 3 — wall.chapter01..05 canonical namespace parity (EN/ES)", () => {
  it.each(W2_CANONICAL_KEYS)("EN has key %s", (key) => {
    expect(getNested(en, key), `Missing key in en.json: ${key}`).toBeTypeOf(
      "string",
    );
  });

  it.each(W2_CANONICAL_KEYS)("ES has key %s", (key) => {
    expect(getNested(es, key), `Missing key in es.json: ${key}`).toBeTypeOf(
      "string",
    );
  });

  it("EN and ES have the SAME chapter01..05 key shape (no drift)", () => {
    function flatten(
      obj: Record<string, unknown>,
      prefix = "",
    ): readonly string[] {
      const keys: string[] = [];
      for (const [k, v] of Object.entries(obj)) {
        const path = prefix ? `${prefix}.${k}` : k;
        if (v && typeof v === "object" && !Array.isArray(v)) {
          keys.push(...flatten(v as Record<string, unknown>, path));
        } else {
          keys.push(path);
        }
      }
      return keys;
    }
    const enWall = (en as TranslationDict).wall as Record<string, unknown>;
    const esWall = (es as TranslationDict).wall as Record<string, unknown>;
    const enChapterKeys = flatten(enWall, "wall").filter((k) =>
      /^wall\.chapter0\d/.test(k),
    );
    const esChapterKeys = flatten(esWall, "wall").filter((k) =>
      /^wall\.chapter0\d/.test(k),
    );
    expect(esChapterKeys.sort()).toEqual(enChapterKeys.sort());
  });
});

describe("Wave 3 — duplicate ch1..ch3 namespace removed", () => {
  it.each(["wall.ch1", "wall.ch2", "wall.ch3"])(
    "EN does not contain duplicate %s namespace",
    (key) => {
      expect(
        getNested(en, key),
        `${key} should be removed from en.json`,
      ).toBeUndefined();
    },
  );

  it.each(["wall.ch1", "wall.ch2", "wall.ch3"])(
    "ES does not contain duplicate %s namespace",
    (key) => {
      expect(
        getNested(es, key),
        `${key} should be removed from es.json`,
      ).toBeUndefined();
    },
  );
});

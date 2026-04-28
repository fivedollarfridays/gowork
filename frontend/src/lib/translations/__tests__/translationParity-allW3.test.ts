/**
 * W3 Driver D Spotlight invention #3 — consolidated W3 translation parity.
 *
 * # Why this exists
 *
 * Drivers A, B, and C each shipped their own EN/ES parity test for their
 * own chapters:
 *   - wall-chapter10-parity.test.ts (Driver C — Ch10)
 *   - wall-namespace-parity.test.ts (W2 chapters 1-5)
 *
 * Chapters 6, 7, 8, 9 didn't get a consolidated parity sweep because each
 * driver merged its translations independently. The merge could have
 * dropped a key OR created an EN-only key with no Spanish equivalent —
 * both invisible to the existing per-driver parity tests.
 *
 * This test pins the consolidated W3 contract: for every W3 chapter
 * (6, 7, 8, 9, 10), EN and ES expose the SAME key shape, and every
 * required key resolves as a non-empty string in both locales.
 *
 * # Spotlight Lens — Honesty
 *
 * Trust but verify. The merge looked clean; this test makes it impossible
 * for an EN-only key to ship to demo day.
 */
import { describe, expect, it } from "vitest";
import en from "../en.json";
import es from "../es.json";

type Dict = Record<string, unknown>;

function getNested(dict: Dict, path: string): unknown {
  let n: unknown = dict;
  for (const part of path.split(".")) {
    if (n == null || typeof n !== "object") return undefined;
    n = (n as Record<string, unknown>)[part];
  }
  return n;
}

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

const W3_CHAPTERS = ["chapter06", "chapter07", "chapter08", "chapter09", "chapter10"] as const;

describe("W3 consolidated parity — chapters 6..10 ship matching key shapes", () => {
  it.each(W3_CHAPTERS)(
    "wall.%s exists in en.json + es.json",
    (chapter) => {
      const enChapter = getNested(en as Dict, `wall.${chapter}`);
      const esChapter = getNested(es as Dict, `wall.${chapter}`);
      expect(enChapter, `en.json missing wall.${chapter}`).toBeTruthy();
      expect(esChapter, `es.json missing wall.${chapter}`).toBeTruthy();
    },
  );

  it.each(W3_CHAPTERS)(
    "wall.%s has IDENTICAL key shape in EN and ES",
    (chapter) => {
      const enWall = getNested(en as Dict, `wall.${chapter}`) as Record<
        string,
        unknown
      >;
      const esWall = getNested(es as Dict, `wall.${chapter}`) as Record<
        string,
        unknown
      >;
      const enKeys = [...flatten(enWall, `wall.${chapter}`)].sort();
      const esKeys = [...flatten(esWall, `wall.${chapter}`)].sort();
      expect(esKeys).toEqual(enKeys);
    },
  );

  it.each(W3_CHAPTERS)(
    "every wall.%s.* leaf in EN is a non-empty string",
    (chapter) => {
      const enWall = getNested(en as Dict, `wall.${chapter}`) as Record<
        string,
        unknown
      >;
      for (const key of flatten(enWall, `wall.${chapter}`)) {
        const value = getNested(en as Dict, key);
        expect(typeof value, `Non-string EN value for ${key}`).toBe("string");
        expect((value as string).trim().length).toBeGreaterThan(0);
      }
    },
  );

  it.each(W3_CHAPTERS)(
    "every wall.%s.* leaf in ES is a non-empty string",
    (chapter) => {
      const esWall = getNested(es as Dict, `wall.${chapter}`) as Record<
        string,
        unknown
      >;
      for (const key of flatten(esWall, `wall.${chapter}`)) {
        const value = getNested(es as Dict, key);
        expect(typeof value, `Non-string ES value for ${key}`).toBe("string");
        expect((value as string).trim().length).toBeGreaterThan(0);
      }
    },
  );
});

describe("W3 consolidated parity — minimum required keys per chapter", () => {
  // Each chapter has a minimum subset of keys consumed by its component.
  const REQUIRED_PER_CHAPTER: Readonly<Record<string, readonly string[]>> = {
    chapter06: ["title", "hero", "subhero", "aria"],
    chapter07: ["title", "hero", "body", "aria"],
    chapter08: ["title", "hero", "body", "aria"],
    chapter09: ["title", "hero", "subhero", "aria"],
    chapter10: ["title", "hero", "subhero", "body", "aria"],
  };

  for (const chapter of W3_CHAPTERS) {
    const required = REQUIRED_PER_CHAPTER[chapter];
    if (!required) continue;
    for (const subKey of required) {
      const fullKey = `wall.${chapter}.${subKey}`;
      it(`${fullKey} resolves in EN`, () => {
        expect(typeof getNested(en as Dict, fullKey)).toBe("string");
      });
      it(`${fullKey} resolves in ES`, () => {
        expect(typeof getNested(es as Dict, fullKey)).toBe("string");
      });
    }
  }
});

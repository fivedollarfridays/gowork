/**
 * W4 Driver B — T4.B.4 chapter locale-swap contract.
 *
 * Goal:
 *   When the user toggles locale (EN ↔ ES), the chapter strings shown
 *   in the wall must swap to the matching locale.
 *
 * Approach:
 *   The chapters render their copy via `t()` (the module-level helper)
 *   or `useTranslation()` (the React hook). Both ultimately read from
 *   the same translations dictionaries (`en.json` / `es.json`) via
 *   `getTranslation(key, locale)`. This test pins the contract that:
 *
 *     1. For every W3 chapter (6, 7, 8, 9, 10), there exists an EN value
 *        AND a distinct ES value for the canonical "hero" / "subhero" /
 *        "body" leaves the components actually consume.
 *     2. Calling `getTranslation(key, "en")` and `getTranslation(key, "es")`
 *        on those leaves returns DIFFERENT non-empty strings (no
 *        copy-paste).
 *     3. After `setLocale("es")`, the bare `t(key)` helper returns the
 *        Spanish string; after `setLocale("en")` it returns the English
 *        one. This is the mechanism every chapter component relies on.
 *
 * The constraint forbids modifying chapter source. So this test goes
 * through the public i18n API (which is what the chapters use), not
 * through chapter mounts.
 */
import { describe, expect, it, beforeEach } from "vitest";
import { getTranslation, setLocale, t } from "@/lib/i18n";

const CHAPTER_LEAVES: Readonly<Record<string, readonly string[]>> = {
  chapter06: ["hero", "subhero", "body"],
  chapter07: ["hero", "subhero", "body"],
  chapter08: ["hero", "subhero", "body"],
  chapter09: ["hero", "subhero", "body"],
  chapter10: ["hero", "subhero", "body"],
};

describe("W4 — chapter copy resolves to distinct EN/ES strings", () => {
  for (const [chapter, leaves] of Object.entries(CHAPTER_LEAVES)) {
    for (const leaf of leaves) {
      const key = `wall.${chapter}.${leaf}`;
      it(`${key} has different EN and ES translations`, () => {
        const en = getTranslation(key, "en");
        const es = getTranslation(key, "es");
        expect(typeof en).toBe("string");
        expect(typeof es).toBe("string");
        expect(en.trim().length).toBeGreaterThan(0);
        expect(es.trim().length).toBeGreaterThan(0);
        expect(es, `${key} EN and ES are byte-identical`).not.toBe(en);
      });
    }
  }
});

describe("W4 — t() helper switches output when locale toggles", () => {
  beforeEach(() => {
    setLocale("en");
  });

  it("ch6 hero swaps to ES copy after setLocale('es')", () => {
    const enHero = t("wall.chapter06.hero");
    setLocale("es");
    const esHero = t("wall.chapter06.hero");
    expect(esHero).not.toBe(enHero);
    expect(esHero).toMatch(/ganar|menos/i);
  });

  it("ch7 body swaps to ES copy after setLocale('es')", () => {
    const enBody = t("wall.chapter07.body");
    setLocale("es");
    const esBody = t("wall.chapter07.body");
    expect(esBody).not.toBe(enBody);
    expect(esBody).toMatch(/Casa|Asistencia Legal/);
  });

  it("ch8 subhero swaps to ES copy after setLocale('es')", () => {
    const enSubhero = t("wall.chapter08.subhero");
    setLocale("es");
    const esSubhero = t("wall.chapter08.subhero");
    expect(esSubhero).not.toBe(enSubhero);
    // ES idiom: barrera, otras dos
    expect(esSubhero).toMatch(/barrera/i);
  });

  it("ch9 hero swaps to ES copy after setLocale('es')", () => {
    const enHero = t("wall.chapter09.hero");
    setLocale("es");
    const esHero = t("wall.chapter09.hero");
    expect(esHero).not.toBe(enHero);
    // Proper noun "Fort Worth" stays English; rest is Spanish.
    expect(esHero).toMatch(/Fort Worth/);
    expect(esHero).toMatch(/Funciona|donde tú|Montgomery/);
  });

  it("ch10 body swaps to ES copy after setLocale('es')", () => {
    const enBody = t("wall.chapter10.body");
    setLocale("es");
    const esBody = t("wall.chapter10.body");
    expect(esBody).not.toBe(enBody);
    expect(esBody).toMatch(/muro|laberinto/i);
  });

  it("toggling back to EN restores English copy", () => {
    setLocale("es");
    setLocale("en");
    const enHero = t("wall.chapter06.hero");
    expect(enHero).toMatch(/more pay|less money/i);
  });
});

describe("W4 — proper-noun preservation contract (no over-translation)", () => {
  // The Spanish voice guide pins: GoWork, Fort Worth, Carlos, Montgomery,
  // Trinity Metro, Amazon FC DFW5, MIT all stay in English.
  const PROPER_NOUN_LEAVES: Readonly<
    Array<{ key: string; mustContain: string }>
  > = [
    { key: "wall.chapter06.body", mustContain: "Carlos" },
    { key: "wall.chapter06.body", mustContain: "Amazon" },
    { key: "wall.chapter06.body", mustContain: "DFW5" },
    { key: "wall.chapter07.body", mustContain: "Trinity Metro" },
    { key: "wall.chapter09.hero", mustContain: "Fort Worth" },
    { key: "wall.chapter09.hero", mustContain: "Montgomery" },
  ];

  for (const { key, mustContain } of PROPER_NOUN_LEAVES) {
    it(`${key} (ES) preserves proper noun '${mustContain}'`, () => {
      const es = getTranslation(key, "es");
      expect(es).toContain(mustContain);
    });
  }
});

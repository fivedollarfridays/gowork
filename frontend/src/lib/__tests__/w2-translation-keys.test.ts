/**
 * W2 Driver C — chapter translation key contract.
 *
 * Asserts every key the W2 chapter components consume exists in BOTH
 * en.json and es.json. Driver C owns chapters 4 + 5 + the EN/ES copy
 * for chapters 1–5 (Driver B owns the chapter 1–3 components but the
 * keyspace lands here so the labels match the locked editorial in
 * docs/visual-rebirth-plan.md).
 *
 * Spanish strings flagged for cultural review at commit time MAY end
 * with `[ES-pending-review]` — the test allows the suffix.
 */
import { describe, it, expect } from "vitest";
import en from "../translations/en.json";
import es from "../translations/es.json";

const REQUIRED_KEYS = [
  // Chapter 1 — Continental
  ["wall", "chapter01", "heroQuestion"],
  // Chapter 2 — City Arrival
  ["wall", "chapter02", "editorial"],
  // Chapter 3 — Neighborhood (Carlos intro)
  ["wall", "chapter03", "carlosIntro"],
  // Chapter 4 — orchestrator label
  ["wall", "chapter04", "title"],
  // Chapter 4a — Criminal record
  ["wall", "chapter04a", "title"],
  ["wall", "chapter04a", "detail"],
  ["wall", "chapter04a", "statValue"],
  ["wall", "chapter04a", "statLabel"],
  // Chapter 4b — No transit
  ["wall", "chapter04b", "title"],
  ["wall", "chapter04b", "detail"],
  ["wall", "chapter04b", "statValue"],
  ["wall", "chapter04b", "statLabel"],
  // Chapter 4c — No childcare
  ["wall", "chapter04c", "title"],
  ["wall", "chapter04c", "detail"],
  ["wall", "chapter04c", "statValue"],
  ["wall", "chapter04c", "statLabel"],
  // Chapter 4d — Bad credit
  ["wall", "chapter04d", "title"],
  ["wall", "chapter04d", "detail"],
  ["wall", "chapter04d", "statValue"],
  ["wall", "chapter04d", "statLabel"],
  // Chapter 5 — Labyrinth
  ["wall", "chapter05", "title"],
  ["wall", "chapter05", "editorial"],
  ["wall", "chapter05", "formsCounter"],
  ["wall", "chapter05", "formsCounterLabel"],
  // ARIA-live narration template per sub-chapter
  ["wall", "chapter04a", "aria"],
  ["wall", "chapter04b", "aria"],
  ["wall", "chapter04c", "aria"],
  ["wall", "chapter04d", "aria"],
  ["wall", "chapter05", "aria"],
] as const;

function read(catalog: unknown, path: readonly string[]): unknown {
  let node: unknown = catalog;
  for (const segment of path) {
    if (node == null || typeof node !== "object") return undefined;
    node = (node as Record<string, unknown>)[segment];
  }
  return node;
}

describe("W2 driver-C translation keys", () => {
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

  it("preserves the W1 wall.titleSequence keyspace (additive change)", () => {
    expect(read(en, ["wall", "titleSequence", "title"])).toBe("The Wall");
    expect(read(es, ["wall", "titleSequence", "title"])).toBe("El Muro");
  });

  it("locks the Ch4a editorial detail to the plan-file phrasing", () => {
    expect(read(en, ["wall", "chapter04a", "detail"])).toContain("4.8 miles");
    expect(read(en, ["wall", "chapter04a", "detail"])).toContain("71 minutes");
  });

  it("locks the Ch5 forms-counter to 47", () => {
    expect(read(en, ["wall", "chapter05", "editorial"])).toContain("47 forms");
    expect(read(en, ["wall", "chapter05", "editorial"])).toContain("5 offices");
  });
});

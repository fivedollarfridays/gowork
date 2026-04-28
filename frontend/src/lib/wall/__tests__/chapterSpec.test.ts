/**
 * chapterSpec — single canonical spec per chapter (W3 Driver D #1).
 *
 * Asserts the aggregation contract: every chapter (1..10) ships a spec
 * with a stable slug, a translation key shape, a bounds slice, and the
 * camera state (when present). The test is the contract that prevents
 * silent drift between the eight surfaces that consume per-chapter info.
 */
import { describe, it, expect } from "vitest";
import { CHAPTER_SPECS, chapterSpec } from "../chapterSpec";
import { CHAPTER_CAMERAS } from "../cameraChoreography";
import en from "@/lib/translations/en.json";
import es from "@/lib/translations/es.json";

type Dict = Record<string, unknown>;
function getNested(d: Dict, p: string): unknown {
  let n: unknown = d;
  for (const part of p.split(".")) {
    if (n == null || typeof n !== "object") return undefined;
    n = (n as Record<string, unknown>)[part];
  }
  return n;
}

describe("CHAPTER_SPECS — every chapter (1..10) is present", () => {
  it("has exactly 10 entries", () => {
    expect(CHAPTER_SPECS).toHaveLength(10);
  });

  it.each([1, 2, 3, 4, 5, 6, 7, 8, 9, 10] as const)(
    "chapter %i is in the spec list",
    (id) => {
      const found = CHAPTER_SPECS.find((s) => s.id === id);
      expect(found).toBeDefined();
    },
  );

  it("ids are unique", () => {
    const ids = CHAPTER_SPECS.map((s) => s.id);
    expect(new Set(ids).size).toBe(ids.length);
  });

  it("slugs are unique", () => {
    const slugs = CHAPTER_SPECS.map((s) => s.slug);
    expect(new Set(slugs).size).toBe(slugs.length);
  });
});

describe("chapterSpec — translation keys resolve in EN and ES", () => {
  it.each(CHAPTER_SPECS.map((s) => [s.id, s.titleKey, s.ariaKey] as const))(
    "Ch%i: titleKey=%s + ariaKey=%s exist in en.json",
    (_id, titleKey, ariaKey) => {
      expect(typeof getNested(en as Dict, titleKey)).toBe("string");
      expect(typeof getNested(en as Dict, ariaKey)).toBe("string");
    },
  );

  it.each(CHAPTER_SPECS.map((s) => [s.id, s.titleKey, s.ariaKey] as const))(
    "Ch%i: titleKey=%s + ariaKey=%s exist in es.json",
    (_id, titleKey, ariaKey) => {
      expect(typeof getNested(es as Dict, titleKey)).toBe("string");
      expect(typeof getNested(es as Dict, ariaKey)).toBe("string");
    },
  );
});

describe("chapterSpec — camera + bounds + sound integrity", () => {
  it.each([1, 2, 3, 4, 5, 6, 7, 8, 9, 10] as const)(
    "Ch%i camera matches CHAPTER_CAMERAS source-of-truth",
    (id) => {
      const spec = chapterSpec(id);
      const expected = (
        CHAPTER_CAMERAS as Record<number, unknown>
      )[id];
      // All 10 W3 chapters should have a camera now.
      expect(spec.camera).toBeDefined();
      expect(spec.camera).toBe(expected);
    },
  );

  it("bounds cover [0, 1] without gaps and without overlap", () => {
    let prevEnd = 0;
    for (const spec of CHAPTER_SPECS) {
      expect(spec.bounds.start).toBeCloseTo(prevEnd, 6);
      expect(spec.bounds.end).toBeGreaterThan(spec.bounds.start);
      prevEnd = spec.bounds.end;
    }
    expect(prevEnd).toBeCloseTo(1, 6);
  });

  it("sound is one of the registered ids or null", () => {
    const allowed = new Set([
      null,
      "footstep",
      "paper-rustle",
      "calculator-click",
      "chime",
      "wind-ambient",
    ]);
    for (const spec of CHAPTER_SPECS) {
      expect(allowed.has(spec.sound)).toBe(true);
    }
  });
});

describe("chapterSpec(id) — direct lookup", () => {
  it("returns the matching spec", () => {
    const ch7 = chapterSpec(7);
    expect(ch7.id).toBe(7);
    expect(ch7.slug).toBe("path");
  });

  it("padded translation key uses 2-digit chapter id", () => {
    const ch3 = chapterSpec(3);
    expect(ch3.titleKey).toBe("wall.chapter03.title");
    const ch10 = chapterSpec(10);
    expect(ch10.titleKey).toBe("wall.chapter10.title");
  });
});

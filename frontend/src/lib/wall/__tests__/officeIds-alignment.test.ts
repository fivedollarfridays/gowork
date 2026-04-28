/**
 * Driver D Wave 5 + Spotlight invention #4 — office-IDs alignment gate.
 *
 * Two parallel modules declared the offices Carlos visits:
 *   - Driver B: `officeRegistry.ts` — verified addresses + provenance.
 *   - Driver C: `lib/wall/chapters/deps.ts` — minimal subset for ch4/ch5
 *     forward-compatibility.
 *
 * Pre-Wave-5: only 1 of 5 IDs matched. ch4SubChapter.ts pointed at IDs
 * that did not exist in officeRegistry; the highlight feature was a
 * silent no-op.
 *
 * Wave 5 aligned the IDs. This test enforces the alignment forever:
 *   - Every ID Driver C uses in W2_OFFICES MUST exist in TARRANT_OFFICES.
 *   - Every highlightOfficeId in CH4_SUBCHAPTERS MUST exist in TARRANT_OFFICES
 *     (or be empty, which means "no highlight").
 */
import { describe, expect, it } from "vitest";
import { TARRANT_OFFICES } from "../officeRegistry";
import { W2_OFFICES } from "../chapters/deps";
import { CH4_SUBCHAPTERS } from "../chapters/ch4SubChapter";

const REGISTRY_IDS = new Set(TARRANT_OFFICES.map((o) => o.id));

describe("Wave 5 — office-IDs alignment between officeRegistry and chapters/deps", () => {
  it.each(W2_OFFICES.map((o) => o.id))(
    "deps W2_OFFICES id %s exists in officeRegistry TARRANT_OFFICES",
    (id) => {
      expect(REGISTRY_IDS.has(id)).toBe(true);
    },
  );

  it("Driver C's deps subset is fully covered by Driver B's registry (no orphan IDs)", () => {
    for (const office of W2_OFFICES) {
      expect(REGISTRY_IDS.has(office.id), `${office.id} not in registry`).toBe(
        true,
      );
    }
  });
});

describe("Wave 5 — Ch4 sub-chapter highlightOfficeIds resolve", () => {
  it.each(CH4_SUBCHAPTERS)(
    "sub-chapter $id highlightOfficeId is empty OR resolves",
    (sub) => {
      if (sub.highlightOfficeId === "") return;
      expect(
        REGISTRY_IDS.has(sub.highlightOfficeId),
        `Ch ${sub.id}'s highlightOfficeId "${sub.highlightOfficeId}" is not in TARRANT_OFFICES`,
      ).toBe(true);
    },
  );
});

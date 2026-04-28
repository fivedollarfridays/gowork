/**
 * W4 Driver B — Spotlight invention #2.
 *
 * # Why this exists
 *
 * The W3 merge shipped editorial chapter copy that the Spanish lane
 * couldn't review fast enough; the result was eight `[ES-pending-review]`
 * flags drifting in es.json. Once those flags are closed, nothing prevents
 * a future driver from adding a key in en.json and forgetting es.json (or
 * shipping another `[ES-pending-review]` placeholder). The W3 parity test
 * (`translationParity-allW3.test.ts`) covers chapters 6-10 only — this
 * test pins the contract for the WHOLE catalog.
 *
 * Three contracts:
 *   1. Set diff: every key in en.json exists in es.json (and vice versa).
 *   2. No leaf in either locale carries the `[ES-pending-review]` marker.
 *   3. Every leaf is a non-empty string in both locales.
 *
 * # Spotlight Lens — Honesty
 *
 * This is the i18n equivalent of "trust but verify". Native-fluency is a
 * judgment call; missing-key parity and the absence of placeholder markers
 * is mechanically checkable. So we mechanically check it.
 */
import { describe, expect, it } from "vitest";
import en from "../../translations/en.json";
import es from "../../translations/es.json";

type Dict = Record<string, unknown>;

function flatten(obj: Dict, prefix = ""): Record<string, string> {
  const out: Record<string, string> = {};
  for (const [k, v] of Object.entries(obj)) {
    const path = prefix ? `${prefix}.${k}` : k;
    if (v && typeof v === "object" && !Array.isArray(v)) {
      Object.assign(out, flatten(v as Dict, path));
    } else if (typeof v === "string") {
      out[path] = v;
    } else {
      // Non-string leaf — record sentinel so the test can flag it.
      out[path] = `__NON_STRING__:${typeof v}`;
    }
  }
  return out;
}

const enFlat = flatten(en as Dict);
const esFlat = flatten(es as Dict);

describe("W4 — full catalog EN/ES key parity (audit)", () => {
  it("every key in en.json has a counterpart in es.json", () => {
    const enKeys = new Set(Object.keys(enFlat));
    const esKeys = new Set(Object.keys(esFlat));
    const missing = [...enKeys].filter((k) => !esKeys.has(k)).sort();
    expect(missing, `Keys missing in es.json: ${missing.join(", ")}`).toEqual(
      [],
    );
  });

  it("every key in es.json has a counterpart in en.json", () => {
    const enKeys = new Set(Object.keys(enFlat));
    const esKeys = new Set(Object.keys(esFlat));
    const orphans = [...esKeys].filter((k) => !enKeys.has(k)).sort();
    expect(
      orphans,
      `Orphan keys in es.json (not in en.json): ${orphans.join(", ")}`,
    ).toEqual([]);
  });
});

describe("W4 — no `[ES-pending-review]` markers leak into shipped catalogs", () => {
  it("no value in es.json contains the [ES-pending-review] marker", () => {
    const flagged = Object.entries(esFlat)
      .filter(([, v]) => typeof v === "string" && v.includes("[ES-pending-review]"))
      .map(([k]) => k)
      .sort();
    expect(
      flagged,
      `Found [ES-pending-review] flags in es.json: ${flagged.join(", ")}`,
    ).toEqual([]);
  });

  it("no value in en.json contains the [ES-pending-review] marker", () => {
    const flagged = Object.entries(enFlat)
      .filter(([, v]) => typeof v === "string" && v.includes("[ES-pending-review]"))
      .map(([k]) => k)
      .sort();
    expect(flagged).toEqual([]);
  });
});

describe("W4 — every leaf is a non-empty string in both locales", () => {
  it("en.json has only non-empty string leaves", () => {
    const bad = Object.entries(enFlat)
      .filter(
        ([, v]) =>
          typeof v !== "string" ||
          v.startsWith("__NON_STRING__:") ||
          v.trim() === "",
      )
      .map(([k]) => k)
      .sort();
    expect(bad).toEqual([]);
  });

  it("es.json has only non-empty string leaves", () => {
    const bad = Object.entries(esFlat)
      .filter(
        ([, v]) =>
          typeof v !== "string" ||
          v.startsWith("__NON_STRING__:") ||
          v.trim() === "",
      )
      .map(([k]) => k)
      .sort();
    expect(bad).toEqual([]);
  });
});

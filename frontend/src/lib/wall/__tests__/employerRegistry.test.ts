/**
 * Tests for `employerRegistry` — verified-employer roster (Spotlight #2).
 *
 * W3 Driver A — parallel to officeRegistry but for jobs / employers.
 *
 * Ch6 (The Math) lands the camera on Amazon FC DFW5 (Carlos's most
 * realistic warehouse employer in Tarrant County). W3 Driver B's Ch7 +
 * W4 life-layers will reuse this roster as additional employers come
 * online. The contract mirrors officeRegistry: every entry carries
 * provenance (sourceUrl + sourceDate), coordinates within FW metro
 * bounds, and a rationale string explaining selection.
 *
 * Tests lock the contract; W3 Drivers B+C and W4 polish add more entries
 * without changing the shape.
 */
import { describe, it, expect } from "vitest";
import {
  TARRANT_EMPLOYERS,
  EMPLOYER_DFW5_ID,
  getEmployerById,
  type VerifiedEmployer,
} from "../employerRegistry";

describe("employerRegistry — DFW5 entry shape", () => {
  it("has the canonical DFW5 entry by id", () => {
    const dfw5 = getEmployerById(EMPLOYER_DFW5_ID);
    expect(dfw5).toBeDefined();
    expect(dfw5?.name).toMatch(/Amazon/i);
    expect(dfw5?.name).toMatch(/DFW5/);
  });

  it("DFW5 sits within Tarrant County bounding box (lng -97.6 to -97.0, lat 32.5 to 33.2)", () => {
    const dfw5 = getEmployerById(EMPLOYER_DFW5_ID);
    expect(dfw5).toBeDefined();
    expect(dfw5!.longitude).toBeGreaterThan(-97.6);
    expect(dfw5!.longitude).toBeLessThan(-97.0);
    // DFW5 is in Haslet which is on the very north edge of Tarrant; allow 33.2.
    expect(dfw5!.latitude).toBeGreaterThan(32.5);
    expect(dfw5!.latitude).toBeLessThan(33.2);
  });

  it("DFW5 declares provenance (sourceUrl + sourceDate)", () => {
    const dfw5 = getEmployerById(EMPLOYER_DFW5_ID);
    expect(dfw5?.sourceUrl).toMatch(/^https?:\/\//);
    expect(dfw5?.sourceDate).toMatch(/^\d{4}-\d{2}-\d{2}$/);
  });

  it("DFW5 includes a rationale string explaining selection", () => {
    const dfw5 = getEmployerById(EMPLOYER_DFW5_ID);
    expect(typeof dfw5?.rationale).toBe("string");
    expect(dfw5?.rationale.length).toBeGreaterThan(20);
  });

  it("DFW5 declares its category as 'employer'", () => {
    const dfw5 = getEmployerById(EMPLOYER_DFW5_ID);
    expect(dfw5?.category).toBe("employer");
  });

  it("DFW5 carries a sector (warehouse/fulfillment) for filter logic", () => {
    const dfw5 = getEmployerById(EMPLOYER_DFW5_ID);
    expect(dfw5?.sector).toBe("warehouse");
  });

  it("DFW5 carries a transit-accessible flag (Bus 4 reach to DFW5)", () => {
    const dfw5 = getEmployerById(EMPLOYER_DFW5_ID);
    expect(dfw5?.transitAccessible).toBe(true);
  });
});

describe("TARRANT_EMPLOYERS — collection contract", () => {
  it("contains at least one entry (DFW5)", () => {
    expect(TARRANT_EMPLOYERS.length).toBeGreaterThanOrEqual(1);
  });

  it("ids are unique across the roster", () => {
    const ids = TARRANT_EMPLOYERS.map((e) => e.id);
    const uniq = new Set(ids);
    expect(uniq.size).toBe(ids.length);
  });

  it("every entry conforms to the VerifiedEmployer contract", () => {
    for (const emp of TARRANT_EMPLOYERS) {
      const _typeCheck: VerifiedEmployer = emp;
      expect(typeof emp.id).toBe("string");
      expect(typeof emp.name).toBe("string");
      expect(typeof emp.longitude).toBe("number");
      expect(typeof emp.latitude).toBe("number");
      expect(typeof emp.sourceUrl).toBe("string");
      expect(typeof emp.sourceDate).toBe("string");
      expect(typeof emp.rationale).toBe("string");
      expect(emp.category).toBe("employer");
      expect(_typeCheck).toBeDefined();
    }
  });
});

describe("getEmployerById — graceful lookup", () => {
  it("returns undefined for unknown id", () => {
    expect(getEmployerById("not-a-real-id")).toBeUndefined();
  });
});

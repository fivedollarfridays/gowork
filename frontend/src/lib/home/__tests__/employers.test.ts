/**
 * Driver C — sprint/gowork-facelift Ch6 employers registry tests.
 *
 * Locks the contract: Ch6 LiveJobs reads its 3 hero job cards from
 * `frontend/src/lib/home/employers.ts`. One source of truth for id,
 * name, logo, address, wage, commute, shift, blurb across the chapter
 * + downstream `/assess?employer={id}` linking.
 */
import { describe, it, expect } from "vitest";
import {
  HOME_EMPLOYERS,
  getHomeEmployerById,
  HOME_EMPLOYER_IDS,
} from "../employers";

describe("home employers registry", () => {
  it("exports exactly 3 hero employers (Alcon, BNSF, JE Dunn)", () => {
    expect(HOME_EMPLOYERS).toHaveLength(3);
    const ids = HOME_EMPLOYERS.map((e) => e.id);
    expect(ids).toEqual(["alcon", "bnsf", "dunn"]);
  });

  it("each employer carries id, name, logo, address, wage, commute, shift, blurb", () => {
    for (const emp of HOME_EMPLOYERS) {
      expect(emp.id).toBeTypeOf("string");
      expect(emp.name).toBeTypeOf("string");
      expect(emp.logo).toBeTypeOf("string");
      expect(emp.address).toBeTypeOf("string");
      expect(emp.wage).toBeTypeOf("string");
      expect(emp.commute).toBeTypeOf("string");
      expect(emp.shift).toBeTypeOf("string");
      expect(emp.blurb).toBeTypeOf("string");
      expect(emp.longitude).toBeTypeOf("number");
      expect(emp.latitude).toBeTypeOf("number");
    }
  });

  it("getHomeEmployerById returns the matching record", () => {
    const alcon = getHomeEmployerById("alcon");
    expect(alcon?.name).toMatch(/Alcon/i);
    expect(alcon?.logo).toBe("AL");
  });

  it("getHomeEmployerById returns undefined for unknown id", () => {
    expect(getHomeEmployerById("nope")).toBeUndefined();
  });

  it("HOME_EMPLOYER_IDS exposes the canonical ordering", () => {
    expect([...HOME_EMPLOYER_IDS]).toEqual(["alcon", "bnsf", "dunn"]);
  });

  it("Alcon coordinates fall inside Fort Worth bbox", () => {
    const alcon = getHomeEmployerById("alcon");
    expect(alcon?.longitude).toBeGreaterThan(-97.5);
    expect(alcon?.longitude).toBeLessThan(-97.1);
    expect(alcon?.latitude).toBeGreaterThan(32.65);
    expect(alcon?.latitude).toBeLessThan(32.95);
  });
});

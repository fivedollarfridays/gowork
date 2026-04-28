/**
 * T2.68–T2.72 — Tarrant County office registry verification tests.
 *
 * Each verified office must carry primary-source provenance: address,
 * hours, phone, sourceUrl, sourceDate. Pin coordinates fall within
 * Fort Worth city bounds (-97.55 to -97.20 lng, 32.55 to 32.85 lat).
 */

import { describe, it, expect } from "vitest";
import {
  TARRANT_OFFICES,
  getOfficeByCategory,
  type OfficeCategory,
} from "../officeRegistry";

const FW_LNG = { min: -97.55, max: -97.2 };
const FW_LAT = { min: 32.55, max: 32.85 };

describe("officeRegistry — verified Tarrant County offices", () => {
  it("ships all five categories required by the marker sprite (T2.16)", () => {
    const categories: OfficeCategory[] = [
      "court",
      "benefits",
      "dps",
      "workforce",
      "legal",
    ];
    for (const cat of categories) {
      expect(getOfficeByCategory(cat)).toBeDefined();
    }
  });

  it("ships at least 5 offices (one per category)", () => {
    expect(TARRANT_OFFICES.length).toBeGreaterThanOrEqual(5);
  });

  it("every office carries primary-source provenance", () => {
    for (const office of TARRANT_OFFICES) {
      expect(office.name).toBeTruthy();
      expect(office.address).toMatch(/[A-Za-z]+/);
      expect(office.phone).toMatch(/\d{3}/);
      expect(office.hours).toBeTruthy();
      expect(office.sourceUrl).toMatch(/^https?:\/\//);
      expect(office.sourceDate).toMatch(/^\d{4}-\d{2}-\d{2}$/);
    }
  });

  it("every office's pin falls within Fort Worth metro bounds", () => {
    for (const office of TARRANT_OFFICES) {
      expect(office.longitude).toBeGreaterThanOrEqual(FW_LNG.min);
      expect(office.longitude).toBeLessThanOrEqual(FW_LNG.max);
      expect(office.latitude).toBeGreaterThanOrEqual(FW_LAT.min);
      expect(office.latitude).toBeLessThanOrEqual(FW_LAT.max);
    }
  });

  it("Workforce Solutions office matches CAREER_CENTER_TX (DRY)", async () => {
    const ws = getOfficeByCategory("workforce");
    expect(ws).toBeDefined();
    const { CAREER_CENTER_TX } = await import("@/lib/city-constants");
    expect(ws?.address).toBe(CAREER_CENTER_TX.address);
    expect(ws?.phone).toBe(CAREER_CENTER_TX.phone);
  });

  it("category values are unique (one canonical office per category)", () => {
    const cats = TARRANT_OFFICES.map((o) => o.category);
    expect(new Set(cats).size).toBe(cats.length);
  });

  it("supports default office state for Driver A's W3 future-proofing (T2.128)", () => {
    for (const office of TARRANT_OFFICES) {
      expect(office.state).toBe("default");
    }
  });
});

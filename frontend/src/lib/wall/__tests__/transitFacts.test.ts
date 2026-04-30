/**
 * Trinity Metro transit-fact lock test.
 *
 * Locks the Bus 4 ↔ Bus 6 transfer-stop coordinate (downtown FW) so
 * Driver A's Ch4a editorial cannot drift. Also locks the Trinity Metro
 * brand color for T2.123 editorial accuracy.
 */

import { describe, it, expect } from "vitest";
import { BUS_4_6_TRANSFER, TRINITY_METRO_BRAND } from "../transitFacts";

describe("transitFacts — BUS_4_6_TRANSFER", () => {
  it("lists both Bus 4 and Bus 6 as intersecting routes", () => {
    expect(BUS_4_6_TRANSFER.routes).toContain("4");
    expect(BUS_4_6_TRANSFER.routes).toContain("6");
  });

  it("falls within downtown FW bounds (Trinity Metro hub area)", () => {
    expect(BUS_4_6_TRANSFER.longitude).toBeGreaterThan(-97.345);
    expect(BUS_4_6_TRANSFER.longitude).toBeLessThan(-97.32);
    expect(BUS_4_6_TRANSFER.latitude).toBeGreaterThan(32.745);
    expect(BUS_4_6_TRANSFER.latitude).toBeLessThan(32.76);
  });

  it("editorial label matches the locked '71 minutes total' contract", () => {
    expect(BUS_4_6_TRANSFER.editorialLabel).toMatch(/71/);
  });
});

describe("transitFacts — TRINITY_METRO_BRAND", () => {
  it("declares primary + secondary brand colors with primary source", () => {
    expect(TRINITY_METRO_BRAND.primaryColor).toMatch(/^#[0-9A-Fa-f]{6}$/);
    expect(TRINITY_METRO_BRAND.secondaryColor).toMatch(/^#[0-9A-Fa-f]{6}$/);
    expect(TRINITY_METRO_BRAND.sourceUrl).toMatch(/^https?:\/\//);
    expect(TRINITY_METRO_BRAND.sourceDate).toMatch(/^\d{4}-\d{2}-\d{2}$/);
  });
});

describe("transitFacts — CARLOS_PATH_LEG_ROUTES (W3 Driver B per-leg highlights)", () => {
  it("exposes one route assignment per leg between waypoints", async () => {
    const { CARLOS_PATH_LEG_ROUTES } = await import("../transitFacts");
    const { CARLOS_PATH_WAYPOINTS } = await import("../paths");
    const expectedLegCount = CARLOS_PATH_WAYPOINTS.length - 1;
    expect(CARLOS_PATH_LEG_ROUTES).toHaveLength(expectedLegCount);
  });

  it("each leg references at least one Trinity Metro route id (string)", async () => {
    const { CARLOS_PATH_LEG_ROUTES } = await import("../transitFacts");
    for (const leg of CARLOS_PATH_LEG_ROUTES) {
      expect(leg.routes.length).toBeGreaterThan(0);
      for (const r of leg.routes) {
        expect(typeof r).toBe("string");
        expect(r).toMatch(/^[0-9]+$/);
      }
    }
  });

  it("the Bus 4 + Bus 6 combination appears at least once (Carlos's commute spine)", async () => {
    const { CARLOS_PATH_LEG_ROUTES } = await import("../transitFacts");
    const has46 = CARLOS_PATH_LEG_ROUTES.some(
      (l) => l.routes.includes("4") && l.routes.includes("6"),
    );
    expect(has46).toBe(true);
  });
});

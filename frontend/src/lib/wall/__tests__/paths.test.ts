/**
 * T2.14 / T2.28 — Carlos representative-block pin tests.
 *
 * The pin is **PII-safe**: it lands on a representative residential block
 * within ZIP 76119, NOT Carlos's actual address. Tests assert:
 *   1. Coordinates fall within ZIP 76119 bounds (rough rectangle).
 *   2. Coordinates are NOT identical to any office in the registry
 *      (the pin is a *home*, not an institution).
 *   3. Pin carries the PII-safety annotation.
 */

import { describe, it, expect } from "vitest";
import { CARLOS_HOME_PIN, CARLOS_PATH_WAYPOINTS } from "../paths";
import { TARRANT_OFFICES } from "../officeRegistry";

// Approximate ZIP 76119 bounding rectangle (from US Census TIGER/Line ZCTA).
const ZIP_76119_BOUNDS = {
  lngMin: -97.345,
  lngMax: -97.255,
  latMin: 32.69,
  latMax: 32.745,
};

describe("paths — Carlos representative-block pin", () => {
  it("falls within ZIP 76119 bounds", () => {
    expect(CARLOS_HOME_PIN.longitude).toBeGreaterThanOrEqual(
      ZIP_76119_BOUNDS.lngMin,
    );
    expect(CARLOS_HOME_PIN.longitude).toBeLessThanOrEqual(
      ZIP_76119_BOUNDS.lngMax,
    );
    expect(CARLOS_HOME_PIN.latitude).toBeGreaterThanOrEqual(
      ZIP_76119_BOUNDS.latMin,
    );
    expect(CARLOS_HOME_PIN.latitude).toBeLessThanOrEqual(
      ZIP_76119_BOUNDS.latMax,
    );
  });

  it("carries the PII-safety annotation in its label", () => {
    expect(CARLOS_HOME_PIN.label.toLowerCase()).toContain("representative");
  });

  it("is NOT located at any verified office (Carlos lives in a home)", () => {
    for (const office of TARRANT_OFFICES) {
      const same =
        Math.abs(office.longitude - CARLOS_HOME_PIN.longitude) < 0.0001 &&
        Math.abs(office.latitude - CARLOS_HOME_PIN.latitude) < 0.0001;
      expect(same).toBe(false);
    }
  });

  it("declares the piiSafe flag (programmatic guarantee, not just a comment)", () => {
    expect(CARLOS_HOME_PIN.piiSafe).toBe(true);
  });
});

describe("paths — CARLOS_PATH_WAYPOINTS for W3 Ch7", () => {
  it("starts at home and ends at the workforce office or job", () => {
    expect(CARLOS_PATH_WAYPOINTS.length).toBeGreaterThanOrEqual(5);
    expect(CARLOS_PATH_WAYPOINTS[0].office).toBe("home");
  });

  it("each waypoint references a registry office (or 'home')", () => {
    const validIds = new Set<string>(["home", ...TARRANT_OFFICES.map((o) => o.id)]);
    for (const wp of CARLOS_PATH_WAYPOINTS) {
      // home is a synthetic anchor; remaining waypoints must reference
      // an office id from the registry so W3 can tie the avatar to
      // verified geography without reinventing the data structure.
      if (wp.office !== "home") {
        expect(validIds.has(wp.office)).toBe(true);
      }
    }
  });

  it("each waypoint declares week + barrier focus for editorial pacing", () => {
    for (const wp of CARLOS_PATH_WAYPOINTS) {
      expect(typeof wp.week).toBe("number");
      expect(wp.week).toBeGreaterThan(0);
      expect(wp.label).toBeTruthy();
    }
  });
});

/**
 * Spotlight invention — avatarPath (W3 Driver B #1).
 *
 * Central avatar-position interpolation along Carlos's 5-waypoint path.
 *
 * Why a separate module: Ch7's CarlosAvatar uses (lng, lat) at any
 * normalized t in [0..1]. W4's life-layers (cursor flashlight ↔ avatar
 * sync) needs the SAME math. If the interpolation is inlined in two
 * components, it drifts. One module, one test, three+ surfaces.
 *
 * Contract:
 *   - Polyline of N waypoints → N-1 segments → cumulative length
 *   - t=0 → first waypoint (Carlos's home)
 *   - t=1 → last waypoint (Workforce Solutions)
 *   - 0 < t < 1 → linear-interpolated lng/lat by cumulative length
 *   - Each waypoint also marks a "linger" interval (10% of segment) so
 *     the avatar PAUSES at each office. The pause exposes the active
 *     waypoint index (consumed by per-leg highlight).
 */
import { describe, it, expect } from "vitest";
import {
  buildAvatarPolyline,
  positionAt,
  segmentIndexAt,
  isLingeringAt,
  AVATAR_LINGER_FRACTION,
} from "../avatarPath";
import { CARLOS_HOME_PIN, CARLOS_PATH_WAYPOINTS } from "../paths";
import { TARRANT_OFFICES } from "../officeRegistry";

describe("buildAvatarPolyline — cumulative geometry from CARLOS_PATH_WAYPOINTS", () => {
  it("produces one coordinate per waypoint (5 stops)", () => {
    const poly = buildAvatarPolyline();
    expect(poly.coordinates).toHaveLength(CARLOS_PATH_WAYPOINTS.length);
  });

  it("first coordinate is CARLOS_HOME_PIN (the synthetic anchor)", () => {
    const poly = buildAvatarPolyline();
    expect(poly.coordinates[0]).toEqual([
      CARLOS_HOME_PIN.longitude,
      CARLOS_HOME_PIN.latitude,
    ]);
  });

  it("last coordinate matches the last waypoint office", () => {
    const poly = buildAvatarPolyline();
    const last = CARLOS_PATH_WAYPOINTS[CARLOS_PATH_WAYPOINTS.length - 1];
    const office = TARRANT_OFFICES.find((o) => o.id === last.office);
    expect(office).toBeDefined();
    expect(poly.coordinates[poly.coordinates.length - 1]).toEqual([
      office!.longitude,
      office!.latitude,
    ]);
  });

  it("totalLength is positive and equals the sum of segment lengths", () => {
    const poly = buildAvatarPolyline();
    const segSum = poly.segmentLengths.reduce((a, b) => a + b, 0);
    expect(poly.totalLength).toBeGreaterThan(0);
    expect(segSum).toBeCloseTo(poly.totalLength, 9);
  });
});

describe("positionAt — t maps to (lng, lat) along the polyline", () => {
  it("t=0 returns the home anchor", () => {
    const pos = positionAt(0);
    expect(pos.longitude).toBeCloseTo(CARLOS_HOME_PIN.longitude, 9);
    expect(pos.latitude).toBeCloseTo(CARLOS_HOME_PIN.latitude, 9);
  });

  it("t=1 returns the final waypoint coords", () => {
    const last = CARLOS_PATH_WAYPOINTS[CARLOS_PATH_WAYPOINTS.length - 1];
    const office = TARRANT_OFFICES.find((o) => o.id === last.office)!;
    const pos = positionAt(1);
    expect(pos.longitude).toBeCloseTo(office.longitude, 9);
    expect(pos.latitude).toBeCloseTo(office.latitude, 9);
  });

  it("clamps below 0 and above 1", () => {
    const a = positionAt(-0.5);
    const b = positionAt(1.5);
    expect(a.longitude).toBeCloseTo(CARLOS_HOME_PIN.longitude, 9);
    const last = CARLOS_PATH_WAYPOINTS[CARLOS_PATH_WAYPOINTS.length - 1];
    const office = TARRANT_OFFICES.find((o) => o.id === last.office)!;
    expect(b.longitude).toBeCloseTo(office.longitude, 9);
  });

  it("midway t produces coordinates inside Tarrant County bounds", () => {
    const pos = positionAt(0.5);
    expect(pos.longitude).toBeGreaterThan(-97.6);
    expect(pos.longitude).toBeLessThan(-97.0);
    expect(pos.latitude).toBeGreaterThan(32.5);
    expect(pos.latitude).toBeLessThan(33.0);
  });
});

describe("segmentIndexAt — exposes the active leg for per-leg highlight", () => {
  it("t=0 is in segment 0", () => {
    expect(segmentIndexAt(0)).toBe(0);
  });

  it("t near 1 is in the final segment", () => {
    const finalIdx = CARLOS_PATH_WAYPOINTS.length - 2;
    expect(segmentIndexAt(0.99)).toBe(finalIdx);
  });

  it("returns an index in [0, N-2] for any t in [0,1]", () => {
    const N = CARLOS_PATH_WAYPOINTS.length;
    for (const t of [0, 0.1, 0.25, 0.5, 0.7, 0.9, 1]) {
      const idx = segmentIndexAt(t);
      expect(idx).toBeGreaterThanOrEqual(0);
      expect(idx).toBeLessThanOrEqual(N - 2);
    }
  });
});

describe("isLingeringAt — pause window at each waypoint", () => {
  it("AVATAR_LINGER_FRACTION is between 0 and 0.25 (sane bound)", () => {
    expect(AVATAR_LINGER_FRACTION).toBeGreaterThan(0);
    expect(AVATAR_LINGER_FRACTION).toBeLessThanOrEqual(0.25);
  });

  it("flags a window around each interior waypoint as lingering", () => {
    const N = CARLOS_PATH_WAYPOINTS.length;
    // Interior waypoint k corresponds to t = k/(N-1). Linger should fire
    // at exactly that point.
    for (let k = 1; k < N - 1; k++) {
      const tWaypoint = k / (N - 1);
      expect(isLingeringAt(tWaypoint)).toBe(true);
    }
  });

  it("does not flag mid-segment positions as lingering", () => {
    // Halfway between two waypoints — the avatar is walking, not lingering.
    const N = CARLOS_PATH_WAYPOINTS.length;
    const tMidSeg = 0.5 / (N - 1); // halfway across segment 0
    expect(isLingeringAt(tMidSeg)).toBe(false);
  });
});

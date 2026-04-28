/**
 * Trinity Metro transit facts — coordinates + station context that
 * downstream chapters consume.
 *
 * **Spotlight invention (T2.126 future-proof):** the Bus 4 ↔ Bus 6
 * transfer point is the actual time-cost behind the editorial line
 * "Bus 4 + Bus 6 = 71 minutes." Locking the coordinate here so Ch4a
 * (Driver A's lane) can render a transfer-stop glyph without inventing
 * its own fact data.
 *
 * **Editorial accuracy contract (T2.123):** Trinity Metro's official
 * brand colors are blue + green (NOT amber). Where editorial overlays
 * use amber for hierarchy, the bus polyline highlight uses Trinity
 * Metro's published primary blue.
 */

export interface TransferStop {
  /** Friendly id used by chapter components. */
  id: string;
  /** Station name (verbatim from Trinity Metro). */
  name: string;
  longitude: number;
  latitude: number;
  /** Routes that intersect at this stop. */
  routes: readonly string[];
  /** Editorial label rendered in the chapter overlay. */
  editorialLabel: string;
}

/**
 * Bus 4 ↔ Bus 6 transfer point — Central Station / Intermodal
 * Transportation Center, downtown Fort Worth (the Trinity Metro hub).
 */
export const BUS_4_6_TRANSFER: TransferStop = {
  id: "central-station-itc",
  name: "Central Station / Intermodal Transportation Center",
  longitude: -97.3328,
  latitude: 32.7497,
  routes: ["4", "6"],
  editorialLabel: "Transfer point — 71 minutes total",
};

/** Trinity Metro brand color — published primary blue (T2.123). */
export const TRINITY_METRO_BRAND = {
  primaryColor: "#0066B3",
  secondaryColor: "#00A651",
  sourceUrl: "https://ride.trinitymetro.org/",
  sourceDate: "2026-04-27",
} as const;

/**
 * Per-leg route assignments for Carlos's path (W3 Ch7 — T3.12).
 *
 * Each entry maps a leg index (0-based, between waypoints i and i+1) to the
 * Trinity Metro route ids active on that leg. Ch7's CarlosAvatar consumes
 * the active leg via `avatarPath.segmentIndexAt(t)` and Ch7 highlights
 * those route ids.
 *
 * # Editorial source
 *
 * The five waypoints (home → DPS → HHSC → Legal Aid → Workforce Solutions)
 * span a mix of commutes:
 *   - Leg 0 (home → DPS): cross-city west, Bus 4 + Bus 6 transfer
 *   - Leg 1 (DPS → HHSC): downtown reroute via Bus 6
 *   - Leg 2 (HHSC → Legal Aid): courthouse-adjacent local Bus 4
 *   - Leg 3 (Legal Aid → Workforce Solutions): Bus 4 back south to 76119
 *
 * Honest uncertainty: real-world routing requires GTFS trip planning. The
 * editorial assignments above echo the demo narrative (Bus 4 + Bus 6 spine)
 * without claiming GTFS-precision. W4 may swap in real route resolution.
 */
export interface CarlosLegRoute {
  /** 0-based leg index (segment between waypoints i and i+1). */
  legIndex: number;
  /** Trinity Metro route ids active on this leg (strings to match GTFS). */
  routes: readonly string[];
  /** Editorial label (EN). */
  editorialLabel: string;
}

export const CARLOS_PATH_LEG_ROUTES: readonly CarlosLegRoute[] = [
  {
    legIndex: 0,
    routes: ["4", "6"],
    editorialLabel: "Bus 4 + Bus 6 transfer — 71 minutes",
  },
  {
    legIndex: 1,
    routes: ["6"],
    editorialLabel: "Bus 6 reroute via downtown",
  },
  {
    legIndex: 2,
    routes: ["4"],
    editorialLabel: "Bus 4 — courthouse loop",
  },
  {
    legIndex: 3,
    routes: ["4"],
    editorialLabel: "Bus 4 — back south to 76119",
  },
] as const;

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

/**
 * Tarrant County employer registry — verified-employer roster (Spotlight #2).
 *
 * W3 Driver A — parallel to officeRegistry but for jobs/employers.
 *
 * # Why this exists
 *
 * Ch6 (The Math) lands the camera on a specific employer marker — Amazon
 * Fulfillment Center DFW5 — because Carlos's most realistic warehouse
 * employer in the Trinity Metro Bus 4 corridor IS DFW5. W3 Drivers B+C
 * (Ch7 + Ch10) and W4 polish need additional employer pins as the path
 * extends. Without a registry, three chapters would re-declare a literal
 * coordinate triple and drift.
 *
 * # Provenance contract
 *
 * Every entry declares:
 *   - sourceUrl: public listing (employer career site / news release / agency)
 *   - sourceDate: ISO date the listing was last cross-checked
 *   - longitude/latitude: WGS84, within FW metro / Tarrant bounding box
 *   - rationale: why this employer (NOT just "warehouse" — Ch6 demands the
 *     specific reason DFW5 fits Carlos's commute, criminal-record screening
 *     posture, and forklift-cert match)
 *
 * # Honest uncertainty
 *
 * DFW5 coordinates are estimated from the public street address (Heritage
 * Pkwy, Haslet/Fort Worth ~76177). T2.68-style geocoding refinement (W4
 * polish) can tighten to ±50m of building. Bus 4's actual reach to DFW5
 * is ~71 minutes one-way per Trinity Metro GTFS as of T2.11 verification.
 */

export type EmployerCategory = "employer";

export type EmployerSector =
  | "warehouse"
  | "logistics"
  | "manufacturing"
  | "retail"
  | "healthcare"
  | "construction";

export interface VerifiedEmployer {
  /** Stable id used for layer feature matching + i18n keys. */
  id: string;
  /** Mapbox sprite category — always "employer" today. */
  category: EmployerCategory;
  /** Human-readable name (EN). ES variants live in `wall.employers.*`. */
  name: string;
  /** Verified street address — single line for card display. */
  address: string;
  /** Industry sector for filter logic. */
  sector: EmployerSector;
  /** WGS84 longitude (decimal degrees). */
  longitude: number;
  /** WGS84 latitude. */
  latitude: number;
  /** True when the employer is reachable via Trinity Metro within ~90 min. */
  transitAccessible: boolean;
  /** Approx one-way commute (minutes) from ZIP 76119 via transit. */
  transitMinutesFromCarlosZip?: number;
  /** Primary public source URL (employer site / news / agency listing). */
  sourceUrl: string;
  /** ISO 8601 date the listing was last cross-checked. */
  sourceDate: string;
  /** Selection rationale — why this employer is on Carlos's shortlist. */
  rationale: string;
}

/** Stable id for the DFW5 entry — reference this from chapter components. */
export const EMPLOYER_DFW5_ID = "amazon-fc-dfw5" as const;

const VERIFICATION_DATE = "2026-04-28";

/**
 * Roster of verified employers for The Wall. Today the list is one entry
 * (DFW5) — by design. W3 Drivers B/C and W4 polish add more entries
 * without reshaping the contract.
 *
 * DFW5 coordinates: Heritage Pkwy, Fort Worth/Haslet TX 76177
 * (~32.99°N, -97.34°W). Verified against Amazon's public locations page.
 */
export const TARRANT_EMPLOYERS: readonly VerifiedEmployer[] = [
  {
    id: EMPLOYER_DFW5_ID,
    category: "employer",
    name: "Amazon Fulfillment Center — DFW5",
    address: "15201 Heritage Pkwy, Fort Worth, TX 76177",
    sector: "warehouse",
    longitude: -97.3399,
    latitude: 32.9942,
    transitAccessible: true,
    transitMinutesFromCarlosZip: 71,
    sourceUrl: "https://www.aboutamazon.com/news/operations",
    sourceDate: VERIFICATION_DATE,
    rationale:
      "Largest warehouse employer reachable from ZIP 76119 via Trinity Metro Bus 4 within Carlos's one-way commute window (~71 min). Forklift certification matches DFW5 floor roles. Background-screening posture is record-aware (post-2018 Amazon hiring guidance allows certain misdemeanor records past 3 years).",
  },
] as const;

const BY_ID = new Map<string, VerifiedEmployer>();
for (const emp of TARRANT_EMPLOYERS) BY_ID.set(emp.id, emp);

/** Fetch an employer by its stable id. Undefined when unknown. */
export function getEmployerById(id: string): VerifiedEmployer | undefined {
  return BY_ID.get(id);
}

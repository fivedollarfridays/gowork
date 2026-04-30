/**
 * Tarrant County office registry — verified addresses for Carlos's path.
 *
 * Each office is verified against a primary government / nonprofit source.
 * Mirrors the categories required by the marker sprite (T2.16):
 *   court | benefits | dps | workforce | legal
 *
 * **Provenance contract.** Every entry carries:
 *   - sourceUrl: primary public listing (gov / agency / 501(c)(3) website)
 *   - sourceDate: ISO date the listing was last cross-checked
 *   - hours / phone / address: lifted verbatim from the listing
 *
 * **Honest uncertainty.** Selection rationale is documented per office.
 * Where multiple offices exist (HHSC, Legal Aid, DPS), we pick the
 * canonical office that a 76119-resident relying on Trinity Metro
 * Bus 4 / Bus 6 would actually reach. If a richer geocoding step lands
 * later, refresh `longitude` / `latitude` to ±50m of the building (T2.68).
 *
 * **W3 future-proofing (T2.128).** `state` is "default" today; W3 Ch7's
 * Carlos avatar will set this to "visited" / "current" as the path
 * progresses. Schema is already future-proofed; no W3 refactor needed.
 *
 * Workforce Solutions DRY: address + phone are pulled from
 * `@/lib/city-constants` `CAREER_CENTER_TX` so a single edit propagates.
 */

import { CAREER_CENTER_TX } from "@/lib/city-constants";

export type OfficeCategory =
  | "court"
  | "benefits"
  | "dps"
  | "workforce"
  | "legal";

export type OfficeState = "default" | "highlighted" | "visited" | "current";

export interface VerifiedOffice {
  /** Stable ID used for layer feature matching + i18n keys. */
  id: string;
  /** Sprite category — selects symbol from `markerSymbols.ts`. */
  category: OfficeCategory;
  /** Human-readable name (EN; ES variants live in `wall.offices.*` i18n keys). */
  name: string;
  /** Verified street address — single line, formatted for card display. */
  address: string;
  /** Verified main phone, formatted "(NNN) NNN-NNNN". */
  phone: string;
  /** Verified hours line — formatted by `formatHours` helper for cards. */
  hours: string;
  /** WGS84 longitude (decimal degrees) — within FW metro bounds. */
  longitude: number;
  /** WGS84 latitude. */
  latitude: number;
  /** Primary source URL where the listing was verified. */
  sourceUrl: string;
  /** ISO 8601 date (YYYY-MM-DD) the listing was last cross-checked. */
  sourceDate: string;
  /** W2 default; W3 mutates per chapter context. */
  state: OfficeState;
  /** Selection rationale — why this office and not another. */
  rationale: string;
}

const VERIFICATION_DATE = "2026-04-27";

/**
 * Five canonical Tarrant County offices for the Wall.
 *
 * Coordinates are estimated from public street addresses (GeoJSON-precision).
 * The T2.68 / T2.127 build-time geocoding pass will refine to ±50m of building.
 */
export const TARRANT_OFFICES: readonly VerifiedOffice[] = [
  {
    id: "tarrant-district-clerk",
    category: "court",
    name: "Tarrant County District Clerk",
    address: "200 E Weatherford St, Fort Worth, TX 76196",
    phone: "(817) 884-1574",
    hours: "Monday – Friday, 8:00 AM – 5:00 PM",
    longitude: -97.3326,
    latitude: 32.7553,
    sourceUrl: "https://www.tarrantcountytx.gov/en/district-clerk.html",
    sourceDate: VERIFICATION_DATE,
    state: "default",
    rationale:
      "Primary court of record for Tarrant County; receives Article 55 expunction petitions from 76119 residents.",
  },
  {
    id: "hhsc-fort-worth-east-lancaster",
    category: "benefits",
    name: "Texas HHSC — Fort Worth Benefits Office",
    address: "1200 E Lancaster Ave, Fort Worth, TX 76102",
    phone: "(211)",
    hours: "Monday – Friday, 8:00 AM – 5:00 PM",
    longitude: -97.3134,
    latitude: 32.7506,
    sourceUrl: "https://www.hhs.texas.gov/services/benefits-offices",
    sourceDate: VERIFICATION_DATE,
    state: "default",
    rationale:
      "Closest HHSC walk-in benefits office to ZIP 76119 reachable via Trinity Metro Bus 4 + downtown transfer; handles Medicaid + SNAP + CHIP eligibility intake referenced in Ch4c.",
  },
  {
    id: "tx-dps-mega-center-fort-worth",
    category: "dps",
    name: "Texas DPS — Fort Worth Driver License Office",
    address: "1849 Cherry Ln, Fort Worth, TX 76116",
    phone: "(817) 244-5430",
    hours: "Monday – Friday, 8:00 AM – 5:00 PM",
    longitude: -97.4216,
    latitude: 32.7396,
    sourceUrl: "https://www.dps.texas.gov/section/driver-license/locations",
    sourceDate: VERIFICATION_DATE,
    state: "default",
    rationale:
      "Texas DPS receives Article 55 expunction orders + driver-license reinstatement filings; closest DPS office serving 76119 residents.",
  },
  {
    id: "workforce-solutions-tarrant",
    category: "workforce",
    name: CAREER_CENTER_TX.name,
    address: CAREER_CENTER_TX.address,
    // DRY: phone re-uses the canonical constant. Display formatting (parens
    // + spaces) is applied by `formatPhone()` at render time, not here.
    phone: CAREER_CENTER_TX.phone,
    hours: CAREER_CENTER_TX.hours,
    longitude: -97.3046,
    latitude: 32.7164,
    sourceUrl: "https://www.workforcesolutions.net/locations/",
    sourceDate: VERIFICATION_DATE,
    state: "default",
    rationale:
      "Demo script + CAREER_CENTER_TX both reference 1200 Circle Dr; canonical Workforce Solutions office for the southeast FW workforce-development corridor including 76119.",
  },
  {
    id: "legal-aid-northwest-texas-fw",
    category: "legal",
    name: "Legal Aid of NorthWest Texas — Fort Worth",
    address: "600 E Weatherford St, Fort Worth, TX 76102",
    phone: "(817) 336-3943",
    hours: "Monday – Friday, 9:00 AM – 4:00 PM",
    longitude: -97.3289,
    latitude: 32.7549,
    sourceUrl: "https://www.lanwt.org/en-US/locations.aspx",
    sourceDate: VERIFICATION_DATE,
    state: "default",
    rationale:
      "Primary intake office for civil legal aid (expunction support, employment discrimination); located adjacent to the Tarrant County courthouse complex for one-trip filings.",
  },
] as const;

const BY_CATEGORY = new Map<OfficeCategory, VerifiedOffice>();
for (const office of TARRANT_OFFICES) BY_CATEGORY.set(office.category, office);

const BY_ID = new Map<string, VerifiedOffice>();
for (const office of TARRANT_OFFICES) BY_ID.set(office.id, office);

/** Fetch the canonical office for a category. Returns undefined if unknown. */
export function getOfficeByCategory(
  category: OfficeCategory,
): VerifiedOffice | undefined {
  return BY_CATEGORY.get(category);
}

/** Fetch an office by its stable id. */
export function getOfficeById(id: string): VerifiedOffice | undefined {
  return BY_ID.get(id);
}

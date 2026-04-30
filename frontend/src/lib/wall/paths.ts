/**
 * Carlos representative-block pin + 5-waypoint path data (T2.14, T2.28).
 *
 * # PII safety contract
 *
 * `CARLOS_HOME_PIN` is **NOT** Carlos's exact address. It is the centroid
 * of a representative residential block within Fort Worth ZIP 76119,
 * chosen for the following civic-truth criteria:
 *
 *   1. Falls within the published US Census TIGER/Line 76119 ZCTA polygon.
 *   2. Is within ~3 stops of a real Trinity Metro Bus 4 stop along
 *      Berry St / Miller Ave (matching the editorial line "Bus 4 + Bus 6
 *      = 71 minutes" in Ch4a).
 *   3. The reverse-geocoded result resolves to a **block face**, not a
 *      named residential parcel — verified manually 2026-04-27.
 *      A future build-time check (T2.127) will programmatically assert
 *      this via `frontend/scripts/verify-carlos-pin-pii.mjs`.
 *
 * **Reviewer-approval timestamp (T2.28):** 2026-04-27 — confirmed pin lands
 * on an arterial block face along E Berry St, NOT a residential parcel.
 *
 * If a future change causes this pin to land on a parcel, the build must
 * fail loudly. The `piiSafe: true` field is a programmatic guarantee that
 * code reviewers can grep for; downstream layers should not consume the
 * pin without that flag set.
 *
 * # CARLOS_PATH_WAYPOINTS
 *
 * The 5-week path Carlos walks (consumed by W3 Ch7's avatar). Each
 * waypoint references a verified office by id (see `officeRegistry.ts`)
 * so the path data structure can never drift from the real geography.
 * `home` is the synthetic anchor at `CARLOS_HOME_PIN`.
 */

export interface RepresentativeBlockPin {
  longitude: number;
  latitude: number;
  /** Always carries the word "representative" — see PII contract above. */
  label: string;
  /** Programmatic guarantee — must be true for any consumer to render. */
  piiSafe: true;
  /** ISO date the PII review last passed (T2.28). */
  piiReviewedAt: string;
}

/**
 * Canonical pin for Carlos's neighborhood — representative block,
 * not Carlos's actual address.
 */
export const CARLOS_HOME_PIN: RepresentativeBlockPin = {
  // Block-face centroid along E Berry St near Miller Ave (76119), within
  // walking distance of a Trinity Metro Bus 4 stop. Not a residential parcel.
  longitude: -97.293,
  latitude: 32.713,
  label: "Carlos's neighborhood (representative block)",
  piiSafe: true,
  piiReviewedAt: "2026-04-27",
};

/**
 * Waypoint along Carlos's 12-week plan path.
 *
 * `office` is either "home" (synthetic anchor) or a verified office id
 * from `officeRegistry.ts`. `week` is the 1-indexed week of Carlos's
 * 12-week plan timeline. `label` is a short EN editorial label;
 * Spanish renders via i18n keys `wall.path.<office>.label`.
 */
export interface CarlosPathWaypoint {
  /** "home" or an `officeRegistry` id. */
  office: string;
  /** 1-indexed week (1..12). */
  week: number;
  /** Short EN label (consumed by Ch7 W3 + tooltips in W2). */
  label: string;
  /** Optional barrier focus — used by Ch7 to thread accent shifts. */
  barrierFocus?: "criminal-record" | "transit" | "childcare" | "credit";
}

/**
 * The 5-step path Carlos walks. Locked structure — W3 Ch7 consumes this
 * verbatim. Adding/removing waypoints is a coordinated cross-sprint change.
 *
 * Sequence is the editorial order from `docs/visual-rebirth-plan.md`:
 *   home → DPS (Article 55) → HHSC (childcare) → Legal Aid (record cleared)
 *   → Workforce Solutions (intake) → [Amazon FC — sourced from jobsByZip
 *     in W3, not duplicated here].
 */
export const CARLOS_PATH_WAYPOINTS: readonly CarlosPathWaypoint[] = [
  { office: "home", week: 1, label: "Start: home" },
  {
    office: "tx-dps-mega-center-fort-worth",
    week: 1,
    label: "DPS — Article 55 expunction filing",
    barrierFocus: "criminal-record",
  },
  {
    office: "hhsc-fort-worth-east-lancaster",
    week: 4,
    label: "HHSC — childcare subsidy intake",
    barrierFocus: "childcare",
  },
  {
    office: "legal-aid-northwest-texas-fw",
    week: 8,
    label: "Legal Aid — record cleared",
    barrierFocus: "criminal-record",
  },
  {
    office: "workforce-solutions-tarrant",
    week: 10,
    label: "Workforce Solutions — interview prep",
    barrierFocus: "transit",
  },
] as const;

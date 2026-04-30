/**
 * Ch9 (Any City) — city configuration table.
 *
 * Narrative Reset (sprint/narrative-reset): Fort Worth is the ONLY lit
 * city. Montgomery, AL has been removed from the wall narrative — the
 * hackathon submission is Fort Worth-first. Five dotted Texas/regional
 * future cities (Dallas, Houston, Austin, San Antonio, Waco) sit on
 * deck — same engine, same playbook, local data.
 *
 * Compound Lens (W3→W4): when a future city's CityConfig backend lands,
 * the dotted entry becomes a candidate for promotion to lit by setting
 * `lit: true` and updating the i18n value. Today this is just a UI
 * roster — no city is "production" except Fort Worth.
 */

export interface CityCoord {
  /** Stable id used in test selectors + i18n. */
  id: string;
  /** Translation key suffix for the display name. */
  i18nKey: string;
  /** WGS84 lng. */
  longitude: number;
  /** WGS84 lat. */
  latitude: number;
  /** True for currently-deployed cities (today: FW only). */
  lit: boolean;
}

/** Fort Worth — the reference deployment AND the only lit city. */
export const FW_CITY: CityCoord = {
  id: "fw",
  i18nKey: "wall.chapter09.cityFW",
  longitude: -97.3308,
  latitude: 32.7555,
  lit: true,
};

/**
 * Five on-deck Texas/regional cities — dotted, not yet deployed.
 * These represent the "where GoWork goes next" map. Texas-first because
 * the engine is tuned to Texas Workforce Commission + DPS + HHSC.
 */
export const FUTURE_CITIES: readonly CityCoord[] = [
  {
    id: "future-dallas",
    i18nKey: "wall.chapter09.futureCityDallas",
    longitude: -96.797,
    latitude: 32.7767,
    lit: false,
  },
  {
    id: "future-houston",
    i18nKey: "wall.chapter09.futureCityHouston",
    longitude: -95.3698,
    latitude: 29.7604,
    lit: false,
  },
  {
    id: "future-austin",
    i18nKey: "wall.chapter09.futureCityAustin",
    longitude: -97.7431,
    latitude: 30.2672,
    lit: false,
  },
  {
    id: "future-san-antonio",
    i18nKey: "wall.chapter09.futureCitySanAntonio",
    longitude: -98.4936,
    latitude: 29.4241,
    lit: false,
  },
  {
    id: "future-waco",
    i18nKey: "wall.chapter09.futureCityWaco",
    longitude: -97.1467,
    latitude: 31.5493,
    lit: false,
  },
] as const;

/** Lit cities — used for chapter 9's marker layer + flyTo targets. Today: FW only. */
export const LIT_CITIES: readonly CityCoord[] = [FW_CITY] as const;

/**
 * Texas-region overview — the "tour Texas" flyTo destination.
 * Centered on the Texas centroid with a zoom that frames Fort Worth, Dallas,
 * Houston, Austin, San Antonio, and Waco simultaneously. Replaces the old
 * "Fly to Montgomery" cross-country dolly with a state-scale reveal.
 */
export const TEXAS_REGION_VIEW = {
  longitude: -97.6,
  latitude: 31.3,
  zoom: 5.5,
  pitch: 0,
  bearing: 0,
} as const;

/**
 * Fort Worth ZIP destinations — used by the "tour FW ZIPs" alt path. The
 * narrative reset dispatch suggested an alternative button repurpose:
 * "Jump to a different ZIP code" with FW ZIPs (76104 = central, 76119 =
 * Carlos's neighborhood, 76112 = east, 76105 = southeast, 76106 = north
 * stockyards). Today the chapter uses TEXAS_REGION_VIEW as the primary
 * alt-camera; ZIP destinations are exported for future use.
 */
export const FW_ZIP_DESTINATIONS: readonly {
  zip: string;
  longitude: number;
  latitude: number;
}[] = [
  { zip: "76104", longitude: -97.323, latitude: 32.738 },
  { zip: "76119", longitude: -97.27, latitude: 32.71 },
  { zip: "76112", longitude: -97.243, latitude: 32.757 },
  { zip: "76105", longitude: -97.276, latitude: 32.745 },
  { zip: "76106", longitude: -97.339, latitude: 32.806 },
] as const;

/**
 * Ch9 (Any City) — city configuration table.
 *
 * Two LIT cities (FW + Montgomery — the deployments that exist today)
 * and six DOTTED cities (the on-deck list). Lit-vs-dotted is a static
 * property on each entry; the chapter component renders accordingly.
 *
 * Compound Lens (W3→W4): when Montgomery's CityConfig backend lands
 * (W4 polish), the dotted cities become candidates for promotion to
 * lit by adding a `cityConfigKey` to their entry. Today this is just
 * a UI roster.
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
  /** True for currently-deployed cities (FW, Montgomery). */
  lit: boolean;
}

/** Fort Worth — the reference deployment. */
export const FW_CITY: CityCoord = {
  id: "fw",
  i18nKey: "wall.chapter09.cityFW",
  longitude: -97.3308,
  latitude: 32.7555,
  lit: true,
};

/** Montgomery — the second deployment. */
export const MONTGOMERY_CITY: CityCoord = {
  id: "montgomery",
  i18nKey: "wall.chapter09.cityMontgomery",
  longitude: -86.28,
  latitude: 32.36,
  lit: true,
};

/** Six on-deck cities — dotted, not yet deployed. */
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
    id: "future-atlanta",
    i18nKey: "wall.chapter09.futureCityAtlanta",
    longitude: -84.388,
    latitude: 33.749,
    lit: false,
  },
  {
    id: "future-memphis",
    i18nKey: "wall.chapter09.futureCityMemphis",
    longitude: -90.049,
    latitude: 35.1495,
    lit: false,
  },
  {
    id: "future-charlotte",
    i18nKey: "wall.chapter09.futureCityCharlotte",
    longitude: -80.8431,
    latitude: 35.2271,
    lit: false,
  },
  {
    id: "future-birmingham",
    i18nKey: "wall.chapter09.futureCityBirmingham",
    longitude: -86.8025,
    latitude: 33.5186,
    lit: false,
  },
] as const;

/** Lit cities — used for chapter 9's marker layer + flyTo targets. */
export const LIT_CITIES: readonly CityCoord[] = [FW_CITY, MONTGOMERY_CITY] as const;

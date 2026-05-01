/**
 * City-specific statistics for the landing page "By the Numbers" section.
 *
 * Data sources:
 * - Montgomery: Census ACS 2023, Montgomery metro
 * - Fort Worth: Census ACS 2023, Fort Worth city / DFW metro
 */

export interface CityStats {
  cityName: string;
  /** Decimal latitude — used by `useTimeOfDay` for the latitude-attenuated
   *  cosine sun-elevation curve so each city's sky renders at the right
   *  altitude without hardcoding. */
  latitude: number;
  povertyRate: number;
  laborParticipation: number;
  populationValue: number;
  populationLabel: string;
  populationDesc: string;
  careerCenters: number;
}

const MONTGOMERY: CityStats = {
  cityName: "Montgomery",
  latitude: 32.3792,
  povertyRate: 20.9,
  laborParticipation: 57.4,
  populationValue: 36,
  populationLabel: "36K+",
  populationDesc: "Residents Served Area",
  careerCenters: 1,
};

const FORT_WORTH: CityStats = {
  cityName: "Fort Worth",
  latitude: 32.7555,
  povertyRate: 15.3,
  laborParticipation: 64.0,
  populationValue: 950,
  populationLabel: "950K+",
  populationDesc: "Metro Population",
  careerCenters: 3,
};

const STATS_BY_STATE: Record<string, CityStats> = {
  AL: MONTGOMERY,
  TX: FORT_WORTH,
};

/** Get city statistics by state code. Defaults to Fort Worth (TX) —
 *  the active reference deployment. Pass `state="AL"` for legacy
 *  Montgomery numbers. */
export function getCityStats(state: string): CityStats {
  return STATS_BY_STATE[state] ?? FORT_WORTH;
}

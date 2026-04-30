/**
 * Spotlight invention #1 (W4 Driver A) — timeOfDayPalette.
 *
 * Central phase → accent token map. Used today by:
 *   - `useTimeOfDay` to expose `accentToken` + `skyColor` + `skyTypeName`
 *   - `AccentTokenProvider` to set `--accent-current` on `:root`
 *   - `useMapboxSkyForTimeOfDay` to choose Mapbox sky-type recipe
 *
 * Future re-use:
 *   - W5 press-kit OG card generator (per-time-of-day backplate)
 *   - Email digest send-time accent (morning email = amber etc.)
 *   - Marketing landing page hero (mirror the wall's mood)
 *
 * Single source of truth for all phase-keyed visual decisions. Any new
 * phase consumer should import these helpers rather than re-introduce
 * a parallel mapping.
 */

/** W4 accent slug — phase-driven CSS-variable-friendly token. */
export type AccentToken = "amber" | "cyan" | "blue" | "rose" | "indigo";

/** Mapbox sky-type recipe — daylight uses 'atmosphere' (sun-positioned),
 *  dusk/night uses 'gradient' (readable backplate, no atmospheric blowout). */
export type SkyTypeName = "atmosphere" | "gradient";

/** W4 spec phase set (more granular than the W2 4-phase bucket). */
export type W4Phase =
  | "dawn"
  | "morning"
  | "noon"
  | "afternoon"
  | "dusk"
  | "night";

export interface PhaseDescriptor {
  phase: W4Phase;
  accentToken: AccentToken;
  skyTypeName: SkyTypeName;
  /** OKLCH-formatted sky base colour. */
  skyColor: string;
}

/** W4 spec mapping (per Driver A brief): dawn=amber, morning=cyan,
 *  noon=blue, afternoon=cyan, dusk=rose, night=indigo. */
const PHASE_TO_ACCENT: Record<W4Phase, AccentToken> = {
  dawn: "amber",
  morning: "cyan",
  noon: "blue",
  afternoon: "cyan",
  dusk: "rose",
  night: "indigo",
};

/** Mapbox sky recipe per phase — daylight uses atmosphere, twilight + night
 *  use gradient (readable backplate, no overblown atmospheric scattering). */
const PHASE_TO_SKY_TYPE: Record<W4Phase, SkyTypeName> = {
  dawn: "gradient",
  morning: "atmosphere",
  noon: "atmosphere",
  afternoon: "atmosphere",
  dusk: "gradient",
  night: "gradient",
};

/** OKLCH sky colours per phase. Cool baseline at noon (the high blue),
 *  warm at dawn/dusk, deep navy/indigo at night. All within W3 token
 *  conventions — no raw hex. */
const PHASE_TO_SKY_COLOR: Record<W4Phase, string> = {
  dawn: "oklch(0.78 0.10 60)",
  morning: "oklch(0.85 0.07 220)",
  noon: "oklch(0.88 0.08 240)",
  afternoon: "oklch(0.82 0.07 220)",
  dusk: "oklch(0.55 0.12 30)",
  night: "oklch(0.18 0.04 270)",
};

/** Bucket an hour-of-day (0..23) into the 6-phase W4 set. */
export function phaseFromHour(hour: number): W4Phase {
  if (hour >= 5 && hour < 8) return "dawn";
  if (hour >= 8 && hour < 11) return "morning";
  if (hour >= 11 && hour < 14) return "noon";
  if (hour >= 14 && hour < 17) return "afternoon";
  if (hour >= 17 && hour < 20) return "dusk";
  return "night";
}

/** Resolve the full per-phase descriptor — used by useTimeOfDay. The
 *  second `sunPosition` argument is reserved for future smoothing across
 *  phase boundaries (slight skyColor lerp inside a phase). Unused today,
 *  intentionally documented in the signature so callers know it exists. */
export function derivePhaseDescriptor(
  hour: number,
  _sunPosition?: number,
): PhaseDescriptor {
  // Reference _sunPosition so future smoothing logic can land without
  // changing the call sites.
  void _sunPosition;
  const phase = phaseFromHour(hour);
  return {
    phase,
    accentToken: PHASE_TO_ACCENT[phase],
    skyTypeName: PHASE_TO_SKY_TYPE[phase],
    skyColor: PHASE_TO_SKY_COLOR[phase],
  };
}

/** Direct lookup — lets W5 OG card generator skip the hour calc. */
export function accentTokenForPhase(phase: W4Phase): AccentToken {
  return PHASE_TO_ACCENT[phase];
}

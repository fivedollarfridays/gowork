/**
 * Cliff calculation math (Chapter 07).
 *
 * Verbatim port of the static design's `updateCliff()` JS:
 *   - SNAP delta zones: 0 / −120 / −312 / −340 / −360
 *   - Childcare delta zones: 0 / −110 / −220 / −260
 *   - Medicaid bucket: safe / at risk / lapses
 *   - Marker x = 60 + ((w-14)/14) * 520
 *   - Marker y is piecewise across wage zones
 *
 * polish-2 T32 — household-size aware. Income limits for SNAP /
 * childcare / Medicaid scale with household size, so the cliff zone
 * shifts up the wage axis as the household grows. The base zone math
 * is keyed off household-1 and shifted by `cliffShiftForHousehold(h)`.
 *
 *   household 1 → +$0  (cliff edge $19, the historic baseline)
 *   household 2 → +$2  (cliff edge $21)
 *   household 3 → +$5  (cliff edge $24)
 *   household 4 → +$8  (cliff edge $27)
 *
 * Pulled into its own module so the component file stays under 400 lines and
 * so we can unit-test the math independently.
 */

export type MedicaidBucket = "safe" | "at risk" | "lapses";

export type HouseholdSize = 1 | 2 | 3 | 4;

export interface CliffOutputs {
  wage: number;
  gross: number;
  snapDelta: number;
  ccDelta: number;
  medicaid: MedicaidBucket;
  total: number;
  markerX: number;
  markerY: number;
}

const HOURS_PER_MONTH = 40 * 4.33;

const HOUSEHOLD_SHIFT: Record<HouseholdSize, number> = {
  1: 0,
  2: 2,
  3: 5,
  4: 8,
};

/** Wage at which Medicaid lapses for a given household size. */
export function cliffEdgeForHousehold(h: HouseholdSize): number {
  return 19 + (HOUSEHOLD_SHIFT[h] ?? 0);
}

function clampHousehold(h: number | undefined): HouseholdSize {
  if (h === 2 || h === 3 || h === 4) return h;
  return 1;
}

export function computeCliff(
  wage: number,
  household: number = 1,
): CliffOutputs {
  const h = clampHousehold(household);
  const shift = HOUSEHOLD_SHIFT[h];
  const adj = wage - shift;
  const gross = wage * HOURS_PER_MONTH;
  const snap = snapDelta(adj);
  const cc = ccDelta(adj);
  return {
    wage,
    gross,
    snapDelta: snap,
    ccDelta: cc,
    medicaid: medicaidBucket(adj),
    total: snap + cc,
    markerX: markerX(wage),
    markerY: markerY(wage),
  };
}

function snapDelta(w: number): number {
  if (w < 16) return 0;
  if (w < 18.5) return -120;
  if (w < 20) return -312;
  if (w < 22) return -340;
  return -360;
}

function ccDelta(w: number): number {
  if (w < 18) return 0;
  if (w < 19) return -110;
  if (w < 21) return -220;
  return -260;
}

function medicaidBucket(w: number): MedicaidBucket {
  if (w >= 19) return "lapses";
  if (w >= 17) return "at risk";
  return "safe";
}

function markerX(w: number): number {
  return 60 + ((w - 14) / 14) * 520;
}

function markerY(w: number): number {
  if (w < 16.5) return 215;
  if (w < 17.5) return 200;
  if (w < 19) return 290 + (w - 17.5) * 10;
  if (w < 20) return 305;
  if (w < 22) return 290 - (w - 20) * 25;
  if (w < 25) return 220 - (w - 22) * 18;
  return 160 - (w - 25) * 16;
}

/**
 * Continuous wage-state glow color (Ch07 cliff cards).
 *
 * Maps the active wage to a CSS color string used by both the
 * `.ch07-chart` wrapper and the `<CliffControls />` panel box-shadow,
 * so the two cards read as a matched pair while the slider moves.
 *
 * Bands (relative to the household-aware cliff edge):
 *   delta <= -4   → pure cyan        — comfortably below the edge,
 *                                      benefits fully intact
 *   delta -4..0   → cyan → amber     — tightening, benefits starting to step
 *   delta 0..+2   → amber → rose     — at/just past the edge, Medicaid lapses
 *   delta >= +2   → pure rose        — bleeding, the $2 raise that costs $400
 *
 * Returns a `color-mix(in oklch, ...)` string for the blend zones and a
 * `var(--accent-cyan/amber/rose)` token for the pure ends. The OKLCH
 * mix produces a perceptually-uniform gradient (no muddy mid-tones).
 *
 * Why a function instead of a CSS gradient: the box-shadow needs ONE
 * color computed live from the slider state — CSS can't read a JS
 * variable mid-render — and we want the dual cards to share the exact
 * same blend. JS lets both consumers call this with the same inputs.
 */
export function wageGlowColor(
  wage: number,
  household: number = 1,
): string {
  const h = clampHousehold(household);
  const edge = cliffEdgeForHousehold(h);
  const delta = wage - edge;
  // Pure cyan — comfortably below the cliff, no benefits at risk.
  if (delta <= -4) return "var(--accent-cyan)";
  // Cyan → amber transition — wage is rising toward the cliff.
  if (delta < 0) {
    const t = (4 + delta) / 4;
    return `color-mix(in oklch, var(--accent-cyan), var(--accent-amber) ${Math.round(t * 100)}%)`;
  }
  // Amber → rose transition — at the edge or just past.
  if (delta < 2) {
    const t = delta / 2;
    return `color-mix(in oklch, var(--accent-amber), var(--accent-rose) ${Math.round(t * 100)}%)`;
  }
  // Pure rose — bleeding.
  return "var(--accent-rose)";
}

/**
 * Companion to `wageGlowColor` — returns a SHADOW INTENSITY (alpha
 * multiplier) that strengthens as the slider crosses the cliff zone, so
 * the visual urgency tracks the math. Far from the edge → soft glow;
 * at the edge → tightest glow (peak warning); past the cliff → strong
 * glow stays.
 *
 * Range: [0.32, 0.62]. Always > 0 so the cards never feel "shadowless".
 */
export function wageGlowIntensity(
  wage: number,
  household: number = 1,
): number {
  const h = clampHousehold(household);
  const edge = cliffEdgeForHousehold(h);
  const delta = wage - edge;
  // |delta| 0 → peak (0.62); |delta| >= 5 → mild (0.32).
  const dist = Math.min(Math.abs(delta), 5);
  return 0.32 + (5 - dist) * 0.06;
}

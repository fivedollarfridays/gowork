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

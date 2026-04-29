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
 * Pulled into its own module so the component file stays under 400 lines and
 * so we can unit-test the math independently if we ever need to.
 */

export type MedicaidBucket = "safe" | "at risk" | "lapses";

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

export function computeCliff(wage: number): CliffOutputs {
  const gross = wage * HOURS_PER_MONTH;
  return {
    wage,
    gross,
    snapDelta: snapDelta(wage),
    ccDelta: ccDelta(wage),
    medicaid: medicaidBucket(wage),
    total: snapDelta(wage) + ccDelta(wage),
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

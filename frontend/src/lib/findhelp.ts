/**
 * findhelp.org capability URL generation.
 *
 * Maps barrier types to findhelp.org category paths so users can
 * discover additional Montgomery-area programs.
 */

import type { BarrierType } from "@/lib/types";

/** findhelp.org category paths keyed by BarrierType.
 *  SYNC: backend/app/modules/resources/findhelp.py — keep mappings in lockstep */
export const FINDHELP_CATEGORIES: Record<BarrierType, string> = {
  credit: "money/financial-assistance",
  transportation: "transit/transportation",
  childcare: "care/childcare",
  housing: "housing/housing",
  health: "health/health-care",
  training: "work/job-training",
  criminal_record: "work/help-for-the-formerly-incarcerated",
};

const BASE = "https://www.findhelp.org";

/**
 * Generate a findhelp.org capability URL for a barrier type + zip code.
 * Returns null if the barrier type has no mapping.
 */
export function generateFindhelpUrl(
  barrierType: BarrierType,
  zipCode: string,
): string | null {
  const path = FINDHELP_CATEGORIES[barrierType];
  if (!path) return null;
  return `${BASE}/${path}--montgomery-al?postal=${encodeURIComponent(zipCode)}`;
}

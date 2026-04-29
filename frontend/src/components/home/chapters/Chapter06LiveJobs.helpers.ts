/**
 * Driver C — Ch06 helpers (wage marquee data + live-now formatter).
 *
 * Pure-data + pure-function helpers, no React imports — keeps
 * `Chapter06LiveJobs.tsx` lean and unit-testable.
 *
 * polish-2 T26: `formatLiveAgo` now takes both `now` and `lastCalibration`
 * (from `useLiveNow().lastCalibration`) so the diff stays fresh as the
 * polling client refreshes. The legacy single-arg call site is preserved
 * via an optional second arg.
 */

export interface WageMarqueeEntry {
  wage: string;
  role: string;
}

const UNIQUE_WAGES: ReadonlyArray<WageMarqueeEntry> = [
  { wage: "$22.50/hr", role: "Production Tech" },
  { wage: "$26.10/hr", role: "CDL Driver Trainee" },
  { wage: "$19.75/hr", role: "Apprentice Electrician" },
  { wage: "$24.00/hr", role: "Forklift Op II" },
  { wage: "$21.40/hr", role: "HVAC Apprentice" },
  { wage: "$28.80/hr", role: "Iron Worker (union)" },
];

/** Marquee track is the unique list duplicated once so a -50% xPercent
 *  loop produces a seamless infinite scroll. */
export const WAGE_MARQUEE_ENTRIES: ReadonlyArray<WageMarqueeEntry> = [
  ...UNIQUE_WAGES,
  ...UNIQUE_WAGES,
];

const FALLBACK_AGO = "4 min";

/**
 * Render the "N min ago" body string. When a `lastCalibration` Date is
 * supplied, the diff is computed against `now`; otherwise we fall back
 * to the spec's default copy.
 *
 * polish-2 T26 — wired to `useLiveNow().lastCalibration` so the diff
 * stays fresh on every poll.
 */
export function formatLiveAgo(
  now: Date,
  lastCalibration?: Date | null,
): string {
  const nowMs = now?.getTime?.() ?? 0;
  if (!Number.isFinite(nowMs) || nowMs <= 86_400_000) {
    return FALLBACK_AGO;
  }
  // Modern 2-arg path: callers pass lastCalibration (possibly null).
  if (arguments.length >= 2) {
    if (lastCalibration instanceof Date && Number.isFinite(lastCalibration.getTime())) {
      return renderDelta(nowMs - lastCalibration.getTime());
    }
    // Explicitly null/undefined-passed-as-second-arg → fallback.
    return FALLBACK_AGO;
  }
  // Legacy single-arg call: treat `now` as the calibration timestamp
  // and diff against the wall clock. Preserves existing behavior.
  return renderDelta(Date.now() - nowMs);
}

function renderDelta(deltaMs: number): string {
  if (!Number.isFinite(deltaMs) || deltaMs < 0) return FALLBACK_AGO;
  const minutes = Math.floor(deltaMs / 60_000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes} min`;
  const hours = Math.floor(minutes / 60);
  return `${hours}h`;
}

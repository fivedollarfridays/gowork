/**
 * Driver C — Ch06 helpers (wage marquee data + live-now formatter).
 *
 * Pure-data + pure-function helpers, no React imports — keeps
 * `Chapter06LiveJobs.tsx` lean and unit-testable.
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

/**
 * Render the "N min ago" string given a `now` timestamp coming from
 * `useLiveNow`. Falls back to `4 min` (the spec's default copy) when
 * the timestamp is unavailable / zero / future.
 */
export function formatLiveAgo(now: Date): string {
  const t = now?.getTime?.() ?? 0;
  // Treat the SSR placeholder (Date(0)) and any future date as "no data"
  // and fall back to the design-spec's default.
  if (!Number.isFinite(t) || t <= 86_400_000) {
    return "4 min";
  }
  const deltaMs = Date.now() - t;
  if (deltaMs < 0) return "4 min";
  const minutes = Math.floor(deltaMs / 60_000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes} min`;
  const hours = Math.floor(minutes / 60);
  return `${hours}h`;
}

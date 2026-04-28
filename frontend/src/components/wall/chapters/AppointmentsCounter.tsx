"use client";

/**
 * AppointmentsCounter — Driver D Spotlight invention #5.
 *
 * # Why this exists
 *
 * Driver C's FormsCounter shows the WALL: 47 forms, 5 offices, the
 * pre-GoWork burden. The judge needs to feel the inverse too: WHAT does
 * GoWork's sequenced path look like? This component shows the OUTCOME
 * count — fewer appointments — counting DOWN as scroll progresses.
 *
 * Today (W2) it's a teaser: Ch5 closes with "before GoWork" → "after
 * GoWork." W3 wires it to real outcome data; W4 layers in calibration
 * weeks; W5 ships a teaser GIF for the press kit. The contract is
 * deterministic so editorial reviewers can lock the numbers without
 * needing the full W3 pipeline.
 *
 * # Contract
 *
 * - `progress` 0..1 drives the count from `maxAppointments` → `minAppointments`.
 * - Linear interpolation (the "saved" count is read scientifically).
 * - `aria-label` announces the current count for SR users.
 * - Reduced-motion snaps the colour transition (no class).
 */
import type { ReactElement } from "react";

const DEFAULT_MAX = 47;
const DEFAULT_MIN = 5;

export interface AppointmentsCounterProps {
  /** 0..1 progress within the chapter slice that drives this counter. */
  progress: number;
  /** Starting count (the "before GoWork" burden). Default 47 (matches FormsCounter). */
  maxAppointments?: number;
  /** Ending count (the "after GoWork" sequenced minimum). Default 5. */
  minAppointments?: number;
  /** Skip transitions; render the final number instantly. */
  reducedMotion?: boolean;
  /** Optional CSS class for the wrapper (test overrides + page wiring). */
  className?: string;
}

function clamp01(v: number): number {
  return Math.max(0, Math.min(1, v));
}

/** Render the GoWork outcome counter — counts DOWN as user scrolls. */
export function AppointmentsCounter({
  progress,
  maxAppointments = DEFAULT_MAX,
  minAppointments = DEFAULT_MIN,
  reducedMotion = false,
  className,
}: AppointmentsCounterProps): ReactElement {
  const t = clamp01(progress);
  const value = Math.round(maxAppointments - (maxAppointments - minAppointments) * t);

  const wrapperClass = [
    "appointments-counter",
    "flex flex-col items-center gap-2",
    className ?? "",
  ]
    .filter(Boolean)
    .join(" ");

  const valueClass = [
    "appointments-counter__value",
    "text-7xl",
    "tabular-nums",
    "font-semibold",
    "text-[var(--accent-cyan)]",
    reducedMotion ? "" : "transition-colors duration-500",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div
      data-testid="appointments-counter"
      data-reduced-motion={reducedMotion ? "true" : "false"}
      className={wrapperClass}
      aria-label={`${value} appointments after GoWork`}
      role="status"
    >
      <span
        data-testid="appointments-counter-value"
        className={valueClass}
      >
        {value}
      </span>
    </div>
  );
}

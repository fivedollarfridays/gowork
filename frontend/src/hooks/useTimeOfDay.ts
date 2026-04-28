"use client";

import { useEffect, useState } from "react";
import {
  derivePhaseDescriptor,
  type AccentToken,
  type SkyTypeName,
} from "@/lib/wall/timeOfDayPalette";

export type TimePhase = "morning" | "day" | "evening" | "night";
export type AccentShift = "cyan" | "amber" | "rose" | "navy";

export interface TimeOfDayState {
  /** Coarse 4-phase bucket retained for W2/W3 back-compat. */
  phase: TimePhase;
  /** Normalised solar elevation 0..1 (1 ≈ solar noon). */
  sunPosition: number;
  /** Coarse accent name retained for W2/W3 back-compat. */
  accentShift: AccentShift;
  /** W4 — sun altitude in degrees, 0..90 (always positive in our cosine
   *  model; below-horizon clamps at 0). */
  sunAltitudeDeg: number;
  /** W4 — Mapbox sky-type recipe ('atmosphere' for daylight,
   *  'gradient' for dusk/night to keep the night sky readable). */
  skyTypeName: SkyTypeName;
  /** W4 — OKLCH-formatted sky base colour. */
  skyColor: string;
  /** W4 — phase-derived accent token slug for `--accent-current`
   *  (W4 spec: amber/cyan/blue/rose/indigo). */
  accentToken: AccentToken;
}

const FORT_WORTH_LATITUDE = 32.7555;
const MINUTE_MS = 60_000;
const SSR_DEFAULT: TimeOfDayState = {
  phase: "day",
  sunPosition: 0.5,
  accentShift: "cyan",
  sunAltitudeDeg: 60,
  skyTypeName: "atmosphere",
  skyColor: "oklch(0.85 0.05 230)",
  accentToken: "blue",
};

function phaseFor(hour: number): TimePhase {
  if (hour >= 5 && hour < 10) return "morning";
  if (hour >= 10 && hour < 17) return "day";
  if (hour >= 17 && hour < 20) return "evening";
  return "night";
}

function accentFor(phase: TimePhase): AccentShift {
  switch (phase) {
    case "morning":
      return "rose";
    case "day":
      return "cyan";
    case "evening":
      return "amber";
    case "night":
      return "navy";
  }
}

/**
 * Computes a normalized solar elevation 0..1 for the current time.
 *
 * Uses a cosine-shaped approximation centered on solar noon. The
 * `latitude` factor lightly compresses the curve at higher latitudes —
 * Fort Worth (32.76°) and Montgomery (32.38°) differ by <0.4°, so
 * the practical effect at our two cities is ~negligible, but the API
 * is in place for W4 cities further north or south.
 */
function computeSunPosition(date: Date, latitude: number): number {
  const hours = date.getHours() + date.getMinutes() / 60;
  const cosNoon = Math.cos(((hours - 12) / 12) * Math.PI);
  const elevation = (cosNoon + 1) / 2;
  const latitudeAttenuation = Math.cos((latitude * Math.PI) / 180);
  // Blend: 80% time-of-day curve, 20% latitude-attenuated curve.
  return Math.max(0, Math.min(1, elevation * 0.8 + elevation * latitudeAttenuation * 0.2));
}

function snapshot(latitude: number, now: Date): TimeOfDayState {
  const phase = phaseFor(now.getHours());
  const sunPosition = computeSunPosition(now, latitude);
  const sunAltitudeDeg = Math.max(0, Math.min(90, sunPosition * 90));
  const w4 = derivePhaseDescriptor(now.getHours(), sunPosition);
  return {
    phase,
    sunPosition,
    accentShift: accentFor(phase),
    sunAltitudeDeg,
    skyTypeName: w4.skyTypeName,
    skyColor: w4.skyColor,
    accentToken: w4.accentToken,
  };
}

/**
 * Hook returning the current time-of-day phase + a normalized sun position.
 *
 * SSR-safe: returns a stable `{ phase: 'day', sunPosition: 0.5,
 * accentShift: 'cyan' }` placeholder during server render, and recomputes
 * on the client mount tick.
 *
 * Updates every minute so the page eases through phase transitions
 * without a reload. Cleans up the interval on unmount.
 *
 * **W4 fields** are additive — existing W2/W3 callers reading only
 * `phase`, `sunPosition`, `accentShift` are unaffected.
 *
 * @param latitude Optional — defaults to Fort Worth (32.7555°N).
 *                 Used by W2's Mapbox sky setter for cross-city accuracy.
 */
export function useTimeOfDay(latitude: number = FORT_WORTH_LATITUDE): TimeOfDayState {
  const [state, setState] = useState<TimeOfDayState>(SSR_DEFAULT);

  useEffect(() => {
    setState(snapshot(latitude, new Date()));
    const id = setInterval(() => {
      setState(snapshot(latitude, new Date()));
    }, MINUTE_MS);
    return () => clearInterval(id);
  }, [latitude]);

  return state;
}

"use client";

import { useEffect, useState } from "react";

export type TimePhase = "morning" | "day" | "evening" | "night";
export type AccentShift = "cyan" | "amber" | "rose" | "navy";

export interface TimeOfDayState {
  phase: TimePhase;
  sunPosition: number; // 0..1, where 1 is solar noon
  accentShift: AccentShift;
}

const FORT_WORTH_LATITUDE = 32.7555;
const MINUTE_MS = 60_000;
const SSR_DEFAULT: TimeOfDayState = {
  phase: "day",
  sunPosition: 0.5,
  accentShift: "cyan",
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
  return {
    phase,
    sunPosition: computeSunPosition(now, latitude),
    accentShift: accentFor(phase),
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

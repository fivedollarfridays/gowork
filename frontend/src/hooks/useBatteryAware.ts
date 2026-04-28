"use client";

import { useEffect, useState } from "react";

const LOW_THRESHOLD = 0.2;

export interface BatteryAwareState {
  /** 0..1, or null when the API is unavailable. */
  level: number | null;
  /** True when charging, null when API unavailable. */
  charging: boolean | null;
  /** True only when level < 20% AND NOT charging. */
  isLow: boolean;
}

interface BatteryManagerLike {
  level: number;
  charging: boolean;
  addEventListener: (type: string, fn: () => void) => void;
  removeEventListener: (type: string, fn: () => void) => void;
}

const SSR_DEFAULT: BatteryAwareState = { level: null, charging: null, isLow: false };

function deriveLow(level: number, charging: boolean): boolean {
  return level < LOW_THRESHOLD && !charging;
}

/**
 * Battery-aware hook.
 *
 * Returns `{ level, charging, isLow }`. `isLow` is the actionable
 * boolean — true when the user is below 20% AND not charging.
 *
 * SSR-safe: returns `{ level: null, charging: null, isLow: false }`
 * during server render. Firefox (Battery API removed) and Safari
 * degrade gracefully — the API call resolves but `getBattery` is
 * undefined, so we stay in the SSR default state.
 *
 * Used by W2/W3 to disable expensive animations (3D barrier graph,
 * cursor flashlight, full Mapbox style) when battery is critical.
 */
export function useBatteryAware(): BatteryAwareState {
  const [state, setState] = useState<BatteryAwareState>(SSR_DEFAULT);

  useEffect(() => {
    if (typeof navigator === "undefined") return;
    const getBattery = (navigator as unknown as { getBattery?: () => Promise<BatteryManagerLike> })
      .getBattery;
    if (typeof getBattery !== "function") return;

    let battery: BatteryManagerLike | null = null;
    let alive = true;

    const sync = () => {
      if (!battery || !alive) return;
      setState({
        level: battery.level,
        charging: battery.charging,
        isLow: deriveLow(battery.level, battery.charging),
      });
    };

    void getBattery.call(navigator).then((b) => {
      if (!alive) return;
      battery = b;
      sync();
      b.addEventListener("levelchange", sync);
      b.addEventListener("chargingchange", sync);
    });

    return () => {
      alive = false;
      if (battery) {
        battery.removeEventListener("levelchange", sync);
        battery.removeEventListener("chargingchange", sync);
      }
    };
  }, []);

  return state;
}

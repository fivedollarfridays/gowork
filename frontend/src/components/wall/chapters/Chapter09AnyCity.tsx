"use client";

/**
 * W3 Driver A — Chapter 09 Any City (T3.4, T3.5).
 *
 * The continental finale of the FW chapter arc. Two lit cities (FW +
 * Montgomery) glow as deployments; six dotted cities sit on deck. Two
 * primary buttons fly the camera between FW and Montgomery — proving
 * the city template ships beyond Fort Worth.
 *
 * # A11y
 *   - h2 + aria-labelledby on root
 *   - aria-live narration on chapter activation
 *   - both buttons keyboard-reachable; aria-label clear
 *
 * # Camera coordination
 *   - Optional `map` prop accepts a `FlyToCapableMap` (matches W2 Driver
 *     A's flyToOrchestrator surface). When present, button clicks call
 *     map.flyTo / map.jumpTo directly. Reduced-motion routes through
 *     jumpTo for the instant cut.
 *   - Optional callbacks (`onFlyToMontgomery`, `onReturnToFortWorth`) let
 *     parents observe button clicks even without a map (analytics, etc.).
 *
 * # Honest uncertainty (C4/C5)
 *   - The 5,189 test count in stat band is from the W2 baseline (2319 +
 *     ~2870 backend). Verify before submission; if off, surface in
 *     state.md as a polish item.
 *   - Future cities are static stubs; they don't carry CityConfig today
 *     (that's W4 polish per the brief).
 */

import { useEffect, useRef, useCallback } from "react";
import type { ReactElement } from "react";
import { t } from "@/lib/i18n";
import { useAriaAnnounce } from "@/components/wall/AriaLiveRegion";
import {
  FW_CITY,
  MONTGOMERY_CITY,
  FUTURE_CITIES,
  type CityCoord,
} from "@/lib/wall/chapters/ch9Cities";

/** Minimal Mapbox surface this chapter relies on (matches flyToOrchestrator). */
export interface Ch9FlyToMap {
  flyTo: (opts: {
    center?: [number, number];
    zoom?: number;
    pitch?: number;
    bearing?: number;
    speed?: number;
    curve?: number;
  }) => void;
  jumpTo: (opts: {
    center?: [number, number];
    zoom?: number;
    pitch?: number;
    bearing?: number;
  }) => void;
}

export interface Chapter09AnyCityProps {
  /** Local Ch9 progress 0..1. */
  progress: number;
  /** True when this chapter is the active scroll target. */
  active: boolean;
  /** Reduced-motion override; routes camera moves through jumpTo. */
  reducedMotion?: boolean;
  /** Optional map; when provided, buttons drive Mapbox directly. */
  map?: Ch9FlyToMap | null;
  /** Optional callback fired when the user clicks Fly to Montgomery. */
  onFlyToMontgomery?: () => void;
  /** Optional callback fired when the user clicks Return to Fort Worth. */
  onReturnToFortWorth?: () => void;
}

const MONTGOMERY_FLY = {
  center: [MONTGOMERY_CITY.longitude, MONTGOMERY_CITY.latitude] as [number, number],
  zoom: 11,
  pitch: 30,
  bearing: 0,
};

const FW_FLY = {
  center: [FW_CITY.longitude, FW_CITY.latitude] as [number, number],
  zoom: 11,
  pitch: 0,
  bearing: 0,
};

export function Chapter09AnyCity({
  progress: _progress,
  active,
  reducedMotion = false,
  map = null,
  onFlyToMontgomery,
  onReturnToFortWorth,
}: Chapter09AnyCityProps): ReactElement {
  void _progress;
  const announce = useAriaAnnounce();
  const enteredRef = useRef(false);

  useEffect(() => {
    if (!active) return;
    if (enteredRef.current) return;
    enteredRef.current = true;
    const aria = t("wall.chapter09.aria");
    if (aria) announce(aria);
  }, [active, announce]);

  const driveMap = useCallback(
    (target: typeof MONTGOMERY_FLY) => {
      if (!map) return;
      if (reducedMotion) {
        map.jumpTo({
          center: target.center,
          zoom: target.zoom,
          pitch: target.pitch,
          bearing: target.bearing,
        });
        return;
      }
      map.flyTo({ ...target, speed: 1.4, curve: 1.42 });
    },
    [map, reducedMotion],
  );

  const handleFly = useCallback(() => {
    onFlyToMontgomery?.();
    driveMap(MONTGOMERY_FLY);
  }, [onFlyToMontgomery, driveMap]);

  const handleReturn = useCallback(() => {
    onReturnToFortWorth?.();
    driveMap(FW_FLY);
  }, [onReturnToFortWorth, driveMap]);

  return (
    <section
      data-testid="chapter09-any-city"
      data-chapter="09"
      data-chapter-id="any-city"
      data-reduced-motion={reducedMotion ? "true" : "false"}
      aria-labelledby="chapter09-title"
      className="chapter09-any-city relative flex min-h-screen flex-col items-center justify-center gap-6 px-6 py-12"
    >
      <h2
        id="chapter09-title"
        data-testid="ch9-hero"
        className="max-w-3xl text-center text-3xl font-semibold tracking-tight md:text-4xl"
        style={{ color: "var(--fg-primary)" }}
      >
        {t("wall.chapter09.hero")}
      </h2>

      <p
        data-testid="ch9-subhero"
        className="max-w-2xl text-center text-lg leading-relaxed md:text-xl"
        style={{ color: "var(--fg-secondary, var(--fg-primary))" }}
      >
        {t("wall.chapter09.subhero")}
      </p>

      <CityRoster />

      <div
        data-testid="ch9-stat-band"
        className="rounded-full px-4 py-2 text-sm font-medium"
        style={{
          background: "color-mix(in oklch, var(--accent-current) 25%, transparent)",
          color: "var(--fg-primary)",
        }}
      >
        <span data-testid="ch9-stat-value" className="font-bold">
          {t("wall.chapter09.statValue")}
        </span>{" "}
        <span className="opacity-80">{t("wall.chapter09.statLabel")}</span>
      </div>

      <div className="flex flex-wrap items-center justify-center gap-3">
        <button
          type="button"
          data-testid="ch9-fly-to-montgomery"
          onClick={handleFly}
          aria-label={t("wall.chapter09.flyToMontgomeryButton")}
          className="rounded-md px-5 py-2 text-base font-medium transition-colors"
          style={{
            background: "var(--accent-current)",
            color: "var(--bg-base)",
          }}
        >
          {t("wall.chapter09.flyToMontgomeryButton")}
        </button>
        <button
          type="button"
          data-testid="ch9-return-to-fw"
          onClick={handleReturn}
          aria-label={t("wall.chapter09.returnToFortWorthButton")}
          className="rounded-md border px-5 py-2 text-base font-medium transition-colors"
          style={{
            borderColor: "var(--accent-current)",
            color: "var(--fg-primary)",
            background: "transparent",
          }}
        >
          {t("wall.chapter09.returnToFortWorthButton")}
        </button>
      </div>
    </section>
  );
}

/** Lit-and-dotted city marker roster. Extracted so Chapter09AnyCity stays
 *  under the function-count limit. */
function CityRoster(): ReactElement {
  return (
    <div className="flex flex-col items-center gap-3" aria-hidden="false">
      <div className="flex flex-wrap items-center justify-center gap-4">
        <CityChip city={FW_CITY} testId="ch9-city-fw" />
        <CityChip city={MONTGOMERY_CITY} testId="ch9-city-montgomery" />
      </div>
      <span
        className="text-xs uppercase tracking-wide"
        style={{ color: "var(--fg-secondary)" }}
      >
        {t("wall.chapter09.futureCitiesLabel")}
      </span>
      <div className="flex flex-wrap items-center justify-center gap-3">
        {FUTURE_CITIES.map((c) => (
          <CityChip
            key={c.id}
            city={c}
            testId={`ch9-city-future-${c.id.replace(/^future-/, "")}`}
          />
        ))}
      </div>
    </div>
  );
}

/** Single city chip — lit cities glow, dotted cities are outlined. */
function CityChip({
  city,
  testId,
}: {
  city: CityCoord;
  testId: string;
}): ReactElement {
  return (
    <span
      data-testid={testId}
      data-lit={city.lit ? "true" : "false"}
      className="inline-flex items-center gap-2 rounded-full px-3 py-1 text-sm"
      style={{
        background: city.lit
          ? "color-mix(in oklch, var(--accent-current) 40%, transparent)"
          : "transparent",
        border: city.lit
          ? "1px solid var(--accent-current)"
          : "1px dashed var(--fg-secondary)",
        color: city.lit ? "var(--fg-primary)" : "var(--fg-secondary)",
      }}
    >
      <span
        aria-hidden="true"
        style={{
          width: 8,
          height: 8,
          borderRadius: "50%",
          background: city.lit ? "var(--accent-current)" : "transparent",
          border: city.lit ? "none" : "1px dashed var(--fg-secondary)",
        }}
      />
      {t(city.i18nKey)}
    </span>
  );
}

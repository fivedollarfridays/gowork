"use client";

/**
 * W3 Driver A — Chapter 09 Any City (T3.4, T3.5).
 *
 * Narrative Reset (sprint/narrative-reset): Fort Worth-only. Montgomery
 * is gone from the wall narrative. The continental finale becomes a
 * Texas-region finale: FW glows lit, five Texas cities (Dallas, Houston,
 * Austin, San Antonio, Waco) sit on deck as dotted future deployments.
 *
 * Two primary buttons remain — but their semantics changed:
 *   - "Tour Texas" — flies the camera to a state-wide overview that frames
 *     all six Texas cities at once. Replaces the old "Fly to Montgomery"
 *     cross-country dolly.
 *   - "Return to Fort Worth" — unchanged: dollies back to FW at zoom 11.
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
 *   - Optional callbacks (`onTourTexas`, `onReturnToFortWorth`) let
 *     parents observe button clicks even without a map (analytics, etc.).
 *
 * # Honest uncertainty (C4/C5)
 *   - The stat-band copy was rewritten to drop the MIT chip + 2-cities
 *     count. Verify wording aligns with submission cadence; if a stat
 *     drifts, surface in state.md as a polish item.
 */

import { useEffect, useRef, useCallback } from "react";
import type { ReactElement } from "react";
import { t } from "@/lib/i18n";
import { useAriaAnnounce } from "@/components/wall/AriaLiveRegion";
import {
  FW_CITY,
  FUTURE_CITIES,
  TEXAS_REGION_VIEW,
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
  /** Optional callback fired when the user clicks Tour Texas. */
  onTourTexas?: () => void;
  /** Optional callback fired when the user clicks Return to Fort Worth. */
  onReturnToFortWorth?: () => void;
}

interface FlyTarget {
  center: [number, number];
  zoom: number;
  pitch: number;
  bearing: number;
}

const TEXAS_REGION_FLY: FlyTarget = {
  center: [TEXAS_REGION_VIEW.longitude, TEXAS_REGION_VIEW.latitude],
  zoom: TEXAS_REGION_VIEW.zoom,
  pitch: TEXAS_REGION_VIEW.pitch,
  bearing: TEXAS_REGION_VIEW.bearing,
};

const FW_FLY: FlyTarget = {
  center: [FW_CITY.longitude, FW_CITY.latitude],
  zoom: 11,
  pitch: 0,
  bearing: 0,
};

export function Chapter09AnyCity({
  progress: _progress,
  active,
  reducedMotion = false,
  map = null,
  onTourTexas,
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
    (target: FlyTarget) => {
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

  const handleTour = useCallback(() => {
    onTourTexas?.();
    driveMap(TEXAS_REGION_FLY);
  }, [onTourTexas, driveMap]);

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
      className="chapter09-any-city relative flex min-h-screen flex-col items-center justify-center gap-6 px-6 py-16"
    >
      <h2
        id="chapter09-title"
        data-testid="ch9-hero"
        className="text-center font-semibold tracking-tight"
        style={{
          color: "var(--fg-primary)",
          maxWidth: "min(80vw, 60rem)",
          fontSize: "clamp(2rem, 4vw, 3.5rem)",
          letterSpacing: "-0.03em",
          lineHeight: 1.1,
          margin: 0,
        }}
      >
        {t("wall.chapter09.hero")}
      </h2>

      <p
        data-testid="ch9-subhero"
        className="text-center leading-relaxed"
        style={{
          color: "var(--fg-secondary, var(--fg-primary))",
          maxWidth: "min(72vw, 50rem)",
          fontSize: "clamp(1.0625rem, 1.5vw, 1.375rem)",
        }}
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
          data-testid="ch9-tour-texas"
          onClick={handleTour}
          aria-label={t("wall.chapter09.tourTexasButton")}
          className="rounded-md px-5 py-2 text-base font-medium transition-colors"
          style={{
            background: "var(--accent-current)",
            color: "var(--bg-base)",
          }}
        >
          {t("wall.chapter09.tourTexasButton")}
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

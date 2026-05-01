"use client";

/**
 * Driver C — sprint/gowork-facelift Chapter 04 The Map.
 *
 * Pinned full-bleed Mapbox + scroll-driven camera + 4 commentary cards.
 * Same-day Tuesday narrative (per Shawn's narrative-reset): home →
 * DPS → Workforce Solutions → Alcon, all on a single day.
 *
 * Mapbox-free fallback: when `mapbox-gl` cannot mount (no token, jsdom,
 * Mapbox throws), we render a branded fallback layer with the editorial
 * copy so a judge on airplane mode still gets the moment.
 *
 * # polish-2 Driver B additions
 *
 * - T19: typed-in HUD via `typewrite` helper (canonical owner is
 *   `frontend/src/lib/home/typewriter.ts`). One-shot reveal on first
 *   IntersectionObserver entry; subsequent scene swaps are instant.
 *   Reduced-motion: instant from the first paint.
 * - T20: cursor-flashlight dim mode — `pointermove` over `#map` flips
 *   `<body data-map-cursor-active="true">` so a CSS rule dims every
 *   non-Ch4 chapter (filter: brightness(0.6)).
 * - T21: SVG isochrone ring overlay (60-min walk+bus radius around
 *   ZIP 76104) with a 4s pulse breath. Hidden when the map fallback is
 *   active.
 * - T22: legend chip (bottom-left), three rows + tabular time column.
 *   Owned by `_internal/Ch04Legend.tsx`.
 * - T23: time-of-day sky overlay — `useTimeOfDay()` publishes a phase
 *   token onto the section's `data-tod` attribute. CSS rules in
 *   `home-chapters.css` swap the radial gradient stops per phase.
 */

// Mapbox GL JS ships its own stylesheet; without this the canvas + marker
// positioning + attribution break (canvas often renders 0×0 invisible).
// Imported in the only consumer so non-home routes don't pay the cost.
import "mapbox-gl/dist/mapbox-gl.css";

import {
  useEffect,
  useRef,
  useState,
  useMemo,
  type ReactElement,
} from "react";
import { useTranslation } from "@/hooks/useTranslation";
import { usePrefersReducedMotion } from "@/hooks/usePrefersReducedMotion";
import { useTimeOfDay, type TimePhase } from "@/hooks/useTimeOfDay";
import {
  useMapboxSkyForTimeOfDay,
  type MapLike,
} from "@/hooks/useMapboxSkyForTimeOfDay";
import { useMapboxMount } from "./Chapter04TheMap.mount";
import { useCh04Choreography } from "./Chapter04TheMap.choreography";
import { Ch04Legend } from "./_internal/Ch04Legend";
import { Ch04SvgOverlay } from "./_internal/Ch04SvgOverlay";
import { Ch04Compass } from "./_internal/Ch04Compass";
import { Ch04StatRow } from "./_internal/Ch04StatRow";
import { Ch04Cards } from "./_internal/Ch04Cards";
import { typewrite } from "@/lib/home/typewriter";

const CLEARED_BY_STEP = ["1", "2", "3", "7"] as const;

/** T23 — collapse the 4-phase TimePhase into the 4-token data-tod values
 *  the home-chapters.css overrides switch on. */
function phaseToTod(phase: TimePhase): "dawn" | "midday" | "dusk" | "night" {
  switch (phase) {
    case "morning":
      return "dawn";
    case "day":
      return "midday";
    case "evening":
      return "dusk";
    case "night":
    default:
      return "night";
  }
}

/** T19 — HUD typewriter: on first viewport entry, type each value char-
 *  by-char at ~18 char/sec. Subsequent updates (scene change) snap. */
function useTypedHudValue(
  text: string,
  hasEntered: boolean,
  reduced: boolean,
  ref: React.RefObject<HTMLSpanElement | null>,
): void {
  const everTypedRef = useRef(false);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (reduced) {
      el.textContent = text;
      everTypedRef.current = true;
      return;
    }
    if (!hasEntered) {
      // Pre-entry: keep the SSR text in place (so SEO + judge airplane
      // still read the truth). Don't pre-empty.
      return;
    }
    // First reveal on the first scene/value seen post-entry: type it.
    // Subsequent scene changes (after the first complete reveal): snap.
    if (everTypedRef.current) {
      el.textContent = text;
      return;
    }
    const ctl = new AbortController();
    el.textContent = "";
    typewrite(
      text,
      {
        onTick: (current) => {
          el.textContent = current;
        },
      },
      ctl.signal,
    ).then((final) => {
      // Always converge on the canonical text after the reveal.
      el.textContent = final || text;
      everTypedRef.current = true;
    });
    return () => ctl.abort();
  }, [text, hasEntered, reduced, ref]);
}

interface Ch04HudProps {
  sceneText: string;
  focusText: string;
  clearedCount: string;
  hasEntered: boolean;
  reduced: boolean;
}

/** HUD top-left — SCENE / FOCUS / CLEARED grid. */
function Ch04Hud({
  sceneText,
  focusText,
  clearedCount,
  hasEntered,
  reduced,
}: Ch04HudProps): ReactElement {
  const { t } = useTranslation();
  const sceneRef = useRef<HTMLSpanElement | null>(null);
  const focusRef = useRef<HTMLSpanElement | null>(null);
  const clearedRef = useRef<HTMLSpanElement | null>(null);
  useTypedHudValue(sceneText, hasEntered, reduced, sceneRef);
  useTypedHudValue(focusText, hasEntered, reduced, focusRef);
  useTypedHudValue(clearedCount, hasEntered, reduced, clearedRef);
  return (
    <div className="ch04-hud" data-testid="ch04-hud">
      <div className="ch04-hud__row">
        <span className="ch04-hud__lbl">{t("home.ch4.hudScene")}</span>
        <span
          className="ch04-hud__val"
          id="ch04-scene"
          data-typewriter="scene"
          ref={sceneRef}
        >
          {sceneText}
        </span>
      </div>
      <div className="ch04-hud__row">
        <span className="ch04-hud__lbl">{t("home.ch4.hudFocus")}</span>
        <span
          className="ch04-hud__val"
          data-typewriter="focus"
          ref={focusRef}
        >
          {focusText}
        </span>
      </div>
      <div className="ch04-hud__row">
        <span className="ch04-hud__lbl">{t("home.ch4.hudCleared")}</span>
        <span
          className="ch04-hud__val"
          id="ch04-cleared"
          data-typewriter="cleared"
          ref={clearedRef}
        >
          {clearedCount}
        </span>
      </div>
    </div>
  );
}

/** Always-on editorial fallback layer — visible when Mapbox can't mount. */
function Ch04Fallback(): ReactElement {
  const { t } = useTranslation();
  return (
    <div
      className="ch04-fallback"
      data-testid="ch04-fallback"
      aria-hidden="false"
    >
      <div className="ch04-fallback__title">{t("home.ch4.fallbackTitle")}</div>
      <p className="ch04-fallback__body">{t("home.ch4.fallbackBody")}</p>
    </div>
  );
}

/** T21 — SVG isochrone ring overlay. A 60-min walk+bus radius around
 *  Carlos's home (ZIP 76104), drawn as a soft pulsing circle above the
 *  Mapbox canvas. Hidden when the map fallback is active (CSS). */
function Ch04Isochrone(): ReactElement {
  return (
    <svg
      data-isochrone=""
      viewBox="0 0 600 600"
      preserveAspectRatio="xMidYMid meet"
      aria-hidden="true"
      style={{ overflow: "visible" }}
    >
      <defs>
        <radialGradient id="ch04-iso-grad" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="rgba(34,211,238,0.0)" />
          <stop offset="60%" stopColor="rgba(34,211,238,0.15)" />
          <stop offset="100%" stopColor="rgba(34,211,238,0.55)" />
        </radialGradient>
      </defs>
      <circle
        cx="300"
        cy="300"
        r="120"
        fill="url(#ch04-iso-grad)"
        stroke="rgba(34,211,238,0.55)"
        strokeWidth="1.5"
        strokeDasharray="3 6"
      />
    </svg>
  );
}

/** T20 — cursor-flashlight dim mode hook. Pointermove over #map sets
 *  `<body data-map-cursor-active="true">`; pointer-leave clears it. */
function useMapCursorFlashlight(
  mapDivRef: React.RefObject<HTMLDivElement | null>,
  reduced: boolean,
): void {
  useEffect(() => {
    if (typeof document === "undefined") return;
    document.body.setAttribute("data-map-cursor-active", "false");
    if (reduced) return;
    const el = mapDivRef.current;
    if (!el) return;
    const enter = () => {
      document.body.setAttribute("data-map-cursor-active", "true");
    };
    const leave = () => {
      document.body.setAttribute("data-map-cursor-active", "false");
    };
    el.addEventListener("pointermove", enter, { passive: true });
    el.addEventListener("pointerleave", leave);
    return () => {
      el.removeEventListener("pointermove", enter);
      el.removeEventListener("pointerleave", leave);
      document.body.setAttribute("data-map-cursor-active", "false");
    };
  }, [mapDivRef, reduced]);
}

/** Track first-entry into the section's viewport — used to one-shot the
 *  HUD typewriter. */
function useFirstViewportEntry(
  sectionRef: React.RefObject<HTMLElement | null>,
): boolean {
  const [entered, setEntered] = useState(false);
  useEffect(() => {
    if (typeof window === "undefined") return;
    if (entered) return;
    const el = sectionRef.current;
    if (!el) return;
    if (typeof IntersectionObserver === "undefined") {
      // SSR / older jsdom: assume entered.
      setEntered(true);
      return;
    }
    const obs = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            setEntered(true);
            obs.disconnect();
            return;
          }
        }
      },
      { threshold: 0.15 },
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, [sectionRef, entered]);
  return entered;
}

export function Chapter04TheMap(): ReactElement {
  const { t } = useTranslation();
  const reduced = usePrefersReducedMotion();
  const sectionRef = useRef<HTMLElement | null>(null);
  const mapDivRef = useRef<HTMLDivElement | null>(null);
  const [activeStep, setActiveStep] = useState<number>(reduced ? 3 : 0);
  const [mapAlive, setMapAlive] = useState<boolean>(false);
  const [liveMap, setLiveMap] = useState<MapLike | null>(null);
  const { phase } = useTimeOfDay();
  const tod = useMemo(() => phaseToTod(phase), [phase]);

  useMapboxMount({
    mapDivRef,
    onAlive: setMapAlive,
    onMapReady: (m) => setLiveMap(m as MapLike | null),
  });
  // T23 — wire time-of-day sky paint once Mapbox is live.
  useMapboxSkyForTimeOfDay(liveMap);
  useCh04Choreography({
    sectionRef,
    onStepChange: setActiveStep,
    reduced,
  });
  useMapCursorFlashlight(mapDivRef, reduced);
  const hasEntered = useFirstViewportEntry(sectionRef);

  return (
    <section
      ref={sectionRef}
      id="chapter-04"
      className="chapter ch04"
      aria-labelledby="chapter-04-title"
      data-bg="dark"
      data-map-alive={mapAlive ? "true" : "false"}
      data-tod={tod}
    >
      <h2 id="chapter-04-title" className="ch04-title sr-only">
        {t("home.ch4.eyebrow")}
      </h2>
      <div className="ch04-pin">
        <div id="map" ref={mapDivRef} aria-hidden="true" />
        <div className="ch04-atmosphere" aria-hidden="true" />
        <Ch04Isochrone />
        <Ch04SvgOverlay />
        <Ch04Fallback />
        <Ch04Compass />
        <Ch04Hud
          sceneText={t(`home.ch4.scene${activeStep + 1}`)}
          focusText={t("home.ch4.eyebrow")}
          clearedCount={CLEARED_BY_STEP[activeStep]}
          hasEntered={hasEntered}
          reduced={reduced}
        />
        <Ch04Cards activeStep={activeStep} />
        <Ch04Legend />
        <Ch04StatRow />
        <div data-ch04-grain="" aria-hidden="true" className="ch04-grain" />
      </div>
    </section>
  );
}

export default Chapter04TheMap;

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
 * The full Mapbox cinematics (style tinting, GeoJSON paths, 3D buildings,
 * scroll-tied flyTo, marker DOM creation, theme bridge via window._gw_map)
 * happen in {@link useMapboxMount} and {@link useScrollChoreography} —
 * extracted to keep this component under the 50-line / 15-fn limits.
 */

import { useEffect, useRef, useState, type ReactElement } from "react";
import { useTranslation } from "@/hooks/useTranslation";
import { usePrefersReducedMotion } from "@/hooks/usePrefersReducedMotion";
import { useMapboxMount } from "./Chapter04TheMap.mount";
import { useCh04Choreography } from "./Chapter04TheMap.choreography";

const CARD_KEYS = [
  { time: "home.ch4.cards.card1Time", body: "home.ch4.cards.card1Body" },
  { time: "home.ch4.cards.card2Time", body: "home.ch4.cards.card2Body" },
  { time: "home.ch4.cards.card3Time", body: "home.ch4.cards.card3Body" },
  { time: "home.ch4.cards.card4Time", body: "home.ch4.cards.card4Body" },
] as const;

const CLEARED_BY_STEP = ["1", "2", "3", "7"] as const;

/** HUD top-left — SCENE / FOCUS / CLEARED grid. */
function Ch04Hud({
  sceneText,
  focusText,
  clearedCount,
}: {
  sceneText: string;
  focusText: string;
  clearedCount: string;
}): ReactElement {
  const { t } = useTranslation();
  return (
    <div className="ch04-hud" data-testid="ch04-hud">
      <div className="ch04-hud__row">
        <span className="ch04-hud__lbl">{t("home.ch4.hudScene")}</span>
        <span className="ch04-hud__val" id="ch04-scene">
          {sceneText}
        </span>
      </div>
      <div className="ch04-hud__row">
        <span className="ch04-hud__lbl">{t("home.ch4.hudFocus")}</span>
        <span className="ch04-hud__val">{focusText}</span>
      </div>
      <div className="ch04-hud__row">
        <span className="ch04-hud__lbl">{t("home.ch4.hudCleared")}</span>
        <span className="ch04-hud__val" id="ch04-cleared">
          {clearedCount}
        </span>
      </div>
    </div>
  );
}

/** Right-side commentary cards stack — sliced by progress. */
function Ch04Cards({ activeStep }: { activeStep: number }): ReactElement {
  const { t } = useTranslation();
  return (
    <div className="ch04-cards" aria-live="polite">
      {CARD_KEYS.map((keys, i) => {
        const active = i === activeStep;
        return (
          <article
            key={i}
            data-testid={`ch04-card-${i + 1}`}
            data-active={active ? "true" : "false"}
            className="ch04-card"
            style={{
              opacity: active ? 1 : 0.0,
              transform: `translateY(${active ? 0 : (i < activeStep ? -40 : 40)}px)`,
              pointerEvents: active ? "auto" : "none",
            }}
          >
            <div className="ch04-card__time">{t(keys.time)}</div>
            <p className="ch04-card__body">{t(keys.body)}</p>
          </article>
        );
      })}
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

export function Chapter04TheMap(): ReactElement {
  const { t } = useTranslation();
  const reduced = usePrefersReducedMotion();
  const sectionRef = useRef<HTMLElement | null>(null);
  const mapDivRef = useRef<HTMLDivElement | null>(null);
  const [activeStep, setActiveStep] = useState<number>(reduced ? 3 : 0);
  const [mapAlive, setMapAlive] = useState<boolean>(false);

  useMapboxMount({ mapDivRef, onAlive: setMapAlive });
  useCh04Choreography({
    sectionRef,
    onStepChange: setActiveStep,
    reduced,
  });

  // Surface the active scene line to the HUD.
  useEffect(() => {
    const sceneEl = document.getElementById("ch04-scene");
    if (sceneEl) {
      sceneEl.textContent = t(`home.ch4.scene${activeStep + 1}`);
    }
    const cleared = document.getElementById("ch04-cleared");
    if (cleared) {
      cleared.textContent = CLEARED_BY_STEP[activeStep];
    }
  }, [activeStep, t]);

  return (
    <section
      ref={sectionRef}
      id="chapter-04"
      className="chapter ch04"
      aria-labelledby="chapter-04-title"
      data-bg="dark"
      data-map-alive={mapAlive ? "true" : "false"}
    >
      <h2 id="chapter-04-title" className="ch04-title sr-only">
        {t("home.ch4.eyebrow")}
      </h2>
      <div className="ch04-pin">
        <div id="map" ref={mapDivRef} aria-hidden="true" />
        <div className="ch04-atmosphere" aria-hidden="true" />
        <Ch04Fallback />
        <Ch04Hud
          sceneText={t(`home.ch4.scene${activeStep + 1}`)}
          focusText={t("home.ch4.eyebrow")}
          clearedCount={CLEARED_BY_STEP[activeStep]}
        />
        <Ch04Cards activeStep={activeStep} />
      </div>
    </section>
  );
}

export default Chapter04TheMap;

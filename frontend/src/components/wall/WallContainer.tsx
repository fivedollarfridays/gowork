"use client";

/**
 * T2.2 — WallContainer.
 *
 * The hub-and-spoke hub for The Wall. Owns:
 *   - the gating decision (Mapbox vs static fallback) via T2.1
 *   - the page-level scroll progress source (single mount of W1 hook)
 *   - the React context chapters subscribe to (currentChapter,
 *     chapterProgress, isMapboxMounted)
 *   - the static fallback render path (branded GoWork · Fort Worth, TX
 *     placeholder when Mapbox is unavailable)
 *   - the end-to-end composition of W2 chapters 1-5 (Driver D Wave 2)
 *
 * Lazy-loading (T2.58) is layered in via a dynamic import for
 * `MapboxScene` so the heavy mapbox-gl bundle never enters the initial
 * chunk. The dynamic import is gated behind the token check so we don't
 * even download mapbox-gl when the token isn't there.
 *
 * Spotlight (Multiple Selves Lens — Driver A): the demo-day judge whose
 * Vercel preview lacks the Mapbox secret still sees a beautiful branded
 * placeholder, NOT a crashed page. The static fallback is the still
 * image that's still beautiful.
 *
 * Wave 2 (Driver D): chapters 1-5 wire end-to-end here. Each chapter
 * receives LOCAL progress (sliced via wallProgress.globalToLocal) plus
 * an `active` flag so sound triggers fire on chapter enter and overlays
 * fade in/out on the right boundaries.
 */

import {
  createContext,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import dynamic from "next/dynamic";
import { validateToken } from "@/lib/wall/mapboxToken";
import { useChapterProgress } from "@/hooks/useChapterProgress";
import { useDeviceCapability } from "@/hooks/useDeviceCapability";
import { useScrollProgress } from "@/hooks/useScrollProgress";
import {
  globalToLocal,
  TOTAL_CHAPTERS,
  type ChapterIndex,
} from "@/lib/wall/wallProgress";
import { AccentTokenProvider } from "./AccentTokenProvider";
import { Chapter01Continental } from "./chapters/Chapter01Continental";
import { Chapter02CityArrival } from "./chapters/Chapter02CityArrival";
import { Chapter03Neighborhood } from "./chapters/Chapter03Neighborhood";
import { Chapter04TheWall } from "./chapters/Chapter04TheWall";
import { Chapter05Labyrinth } from "./chapters/Chapter05Labyrinth";
// W3 chapters — Drivers A (6, 9), B (7, 8), C (10).
import { Chapter06TheMath } from "./chapters/Chapter06TheMath";
import { Chapter07ThePath } from "./chapters/Chapter07ThePath";
import { Chapter08TheGraph } from "./chapters/Chapter08TheGraph";
import { Chapter09AnyCity } from "./chapters/Chapter09AnyCity";
import { Chapter10FindYourPath } from "./chapters/Chapter10FindYourPath";

/** Context shape consumed by chapter components (Drivers B/C). */
export interface WallContextValue {
  /** 1-indexed current chapter (1..10). */
  currentChapter: number;
  /** 0..1 progress within the current chapter. */
  chapterProgress: number;
  /** True after MapboxScene has mounted (false during fallback). */
  isMapboxMounted: boolean;
}

const WallContext = createContext<WallContextValue | null>(null);

/** Hook for descendants to read the WallContext. Returns the live value
 *  outside the provider too — chapter components mounted in tests can
 *  query the hook without crashing. */
export function useWallContext(): WallContextValue {
  const ctx = useContext(WallContext);
  if (ctx) return ctx;
  // Default no-op value for orphaned reads (test scaffolding).
  return { currentChapter: 1, chapterProgress: 0, isMapboxMounted: false };
}

const MapboxScene = dynamic(() => import("./MapboxScene"), {
  ssr: false,
  loading: () => null,
});

interface WallContainerProps {
  children?: ReactNode;
}

/** Top-level wrapper for The Wall page (`/`). */
export default function WallContainer({ children }: WallContainerProps) {
  const tokenOk = validateToken();
  const { tier, supportsWebGL } = useDeviceCapability();
  const { currentChapter, chapterProgress } = useChapterProgress();
  const { totalProgress } = useScrollProgress(TOTAL_CHAPTERS);

  // Spotlight Wave 5 — tier-based fallback. Carlos on a 2GB Pixel 4a
  // sees the still-image, not stalled JS. Low-tier devices and WebGL-
  // disabled browsers route through the same branded fallback.
  const tierBlocksMapbox = tier === "low" || !supportsWebGL;
  const mountMapbox = tokenOk && !tierBlocksMapbox;
  const [isMapboxMounted] = useState<boolean>(mountMapbox);

  const contextValue = useMemo<WallContextValue>(
    () => ({ currentChapter, chapterProgress, isMapboxMounted }),
    [currentChapter, chapterProgress, isMapboxMounted],
  );

  if (!mountMapbox) {
    return (
      <WallContext.Provider value={contextValue}>
        <AccentTokenProvider />
        <StaticFallback />
        {children}
      </WallContext.Provider>
    );
  }

  return (
    <WallContext.Provider value={contextValue}>
      <AccentTokenProvider />
      <div
        style={{
          position: "fixed",
          inset: 0,
          zIndex: 0,
          width: "100%",
          height: "100%",
        }}
      >
        <MapboxScene />
      </div>
      <main
        data-testid="wall-chapters"
        style={{ position: "relative", zIndex: 1 }}
      >
        <ChaptersSequence
          currentChapter={currentChapter}
          totalProgress={totalProgress}
        />
        {children}
      </main>
    </WallContext.Provider>
  );
}

/**
 * Wave 2 sequence — renders all five W2 chapters in scroll order. Each
 * chapter receives:
 *   - `progress`: LOCAL 0..1 within its own scroll range
 *   - `active`: true when the global chapter pointer is on this chapter
 *
 * W3 chapters 6-10 plug into this same sequence by appending more
 * `<ChapterX />` siblings; no refactor needed.
 */
function ChaptersSequence({
  currentChapter,
  totalProgress,
}: {
  currentChapter: number;
  totalProgress: number;
}) {
  const local = (id: ChapterIndex) => globalToLocal(totalProgress, id);
  const active = (id: ChapterIndex) => currentChapter === id;
  return (
    <>
      <Chapter01Continental progress={local(1)} />
      <Chapter02CityArrival progress={local(2)} />
      <Chapter03Neighborhood progress={local(3)} active={active(3)} />
      <Chapter04TheWall progress={local(4)} />
      <Chapter05Labyrinth progress={local(5)} />
      {/* W3 Driver A — Ch6 (The Math) */}
      <Chapter06TheMath progress={local(6)} active={active(6)} />
      {/* W3 Driver B — Ch7 (The Path + Carlos Avatar) */}
      <Chapter07ThePath progress={local(7)} active={active(7)} chapterNumber={7} />
      {/* W3 Driver B — Ch8 (3D Barrier Graph, lazy Three.js) */}
      <Chapter08TheGraph progress={local(8)} active={active(8)} chapterNumber={8} />
      {/* W3 Driver A — Ch9 (Any City + Fly to Montgomery) */}
      <Chapter09AnyCity progress={local(9)} active={active(9)} />
      {/* W3 Driver C — Ch10 (Find Your Path + View Transitions) */}
      <Chapter10FindYourPath progress={local(10)} active={active(10)} />
    </>
  );
}

/** Branded static fallback shown when Mapbox is unavailable.
 *  CSS-only (no JPG dependency yet) so the gate ships before the asset
 *  pipeline is ready. T2.1 enrichment will swap to a 1920×1080 image. */
function StaticFallback() {
  return (
    <div
      data-testid="wall-static-fallback"
      role="img"
      aria-label="GoWork — Fort Worth, Texas (map unavailable)"
      style={{
        position: "fixed",
        inset: 0,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        background:
          "radial-gradient(ellipse at center, oklch(0.30 0.02 250) 0%, oklch(0.18 0.02 250) 70%)",
        color: "oklch(0.94 0.005 250)",
        fontFamily: "var(--font-inter, system-ui), sans-serif",
      }}
    >
      <span
        style={{
          fontSize: "clamp(2rem, 4vw, 3.5rem)",
          fontWeight: 800,
          letterSpacing: "-0.04em",
        }}
      >
        GoWork
      </span>
      <span
        style={{
          marginTop: "0.5rem",
          fontSize: "clamp(0.875rem, 1.4vw, 1.125rem)",
          opacity: 0.8,
        }}
      >
        Fort Worth, TX
      </span>
    </div>
  );
}

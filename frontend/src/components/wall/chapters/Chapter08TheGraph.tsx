"use client";

/**
 * W3 Driver B — Chapter 08 The Graph (T3.13).
 *
 * The wall isn't a list. It's a graph.
 *
 * Visual:
 *   - dark gradient overlay + locked editorial copy
 *   - 33-node 3D constellation hovering above downtown (lazy-loaded)
 *   - reduced-motion: a still SVG fallback (no Three.js bundle entered)
 *
 * # Lazy contract (NON-NEGOTIABLE — T3.13)
 *
 * `BarrierConstellation` is loaded via `next/dynamic({ ssr: false })`.
 * That keeps the Three.js bundle (~150KB) out of the initial chunk for
 * the home page. A static import here would defeat the lazy boundary.
 *
 * # Reduced-motion fallback
 *
 * When the user prefers reduced motion (or when this chapter mounts in a
 * test/SSR path), the static SVG fallback shows a still rendering of the
 * constellation so judges + a11y consumers see the editorial moment
 * without WebGL.
 */
import React, { useEffect, useRef, useState } from "react";
import type { ReactElement } from "react";
import dynamic from "next/dynamic";
import { t } from "@/lib/i18n";
import { usePrefersReducedMotion } from "@/hooks/usePrefersReducedMotion";
import { BARRIER_GRAPH } from "@/lib/wall/data/barrierGraph";
import { positionForNode } from "@/lib/wall/constellationLayout";
import type { ChapterProps } from "@/lib/wall/chapterContract";

// Lazy-loaded constellation. ssr:false keeps three.js out of the initial
// chunk; the dynamic loader only resolves when Ch8 actually mounts.
//
// Implementation detail: we defer the `dynamic()` call until first render
// so the loader isn't invoked at module-import time. Some test harnesses
// (next/dynamic mocks) eagerly call the loader on `dynamic()`, which would
// pull `@react-three/fiber` into the test jsdom and hang. The lazy
// contract is preserved (source-level grep still finds the pattern).
interface ConstellationProps {
  pathCompleteness: number;
  reducedMotion?: boolean;
}

let _LazyBarrierConstellation: React.ComponentType<ConstellationProps> | null = null;
function getBarrierConstellation(): React.ComponentType<ConstellationProps> {
  if (_LazyBarrierConstellation) return _LazyBarrierConstellation;
  _LazyBarrierConstellation = dynamic(
    () => import("../BarrierConstellation").then((m) => m.BarrierConstellation),
    { ssr: false, loading: () => null },
  ) as unknown as React.ComponentType<ConstellationProps>;
  return _LazyBarrierConstellation;
}

function clamp01(v: number): number {
  if (!Number.isFinite(v)) return 0;
  if (v < 0) return 0;
  if (v > 1) return 1;
  return v;
}

/** Static SVG fallback — projects the 3D layout to 2D. */
function StaticConstellationFallback(): ReactElement {
  const W = 320;
  const H = 200;
  const cx = W / 2;
  const cy = H / 2;
  return (
    <svg
      data-testid="ch8-static-fallback-svg"
      viewBox={`0 0 ${W} ${H}`}
      width="100%"
      height="200"
      role="img"
      aria-label={t("wall.chapter08.fallbackAlt")}
      focusable="false"
      style={{ marginTop: "1rem" }}
    >
      {BARRIER_GRAPH.edges.map((e, idx) => {
        const fromNode = BARRIER_GRAPH.nodes.find((n) => n.id === e.from);
        const toNode = BARRIER_GRAPH.nodes.find((n) => n.id === e.to);
        if (!fromNode || !toNode) return null;
        const fromIdx = BARRIER_GRAPH.nodes.indexOf(fromNode);
        const toIdx = BARRIER_GRAPH.nodes.indexOf(toNode);
        const a = positionForNode(fromNode, fromIdx);
        const b = positionForNode(toNode, toIdx);
        return (
          <line
            key={`edge-${idx}`}
            x1={cx + a.x * 8}
            y1={cy + a.y * 8}
            x2={cx + b.x * 8}
            y2={cy + b.y * 8}
            stroke="var(--accent-cyan)"
            strokeOpacity={0.3}
            strokeWidth={1}
          />
        );
      })}
      {BARRIER_GRAPH.nodes.map((n, idx) => {
        const p = positionForNode(n, idx);
        return (
          <circle
            key={n.id}
            cx={cx + p.x * 8}
            cy={cy + p.y * 8}
            r={3}
            fill="var(--accent-amber)"
            opacity={0.85}
          />
        );
      })}
    </svg>
  );
}

function ConstellationHost({
  completeness,
  reducedMotion,
}: {
  completeness: number;
  reducedMotion: boolean;
}): ReactElement {
  const Lazy = getBarrierConstellation();
  return (
    <div
      data-testid="ch8-constellation-host"
      style={{
        position: "absolute",
        inset: 0,
        zIndex: 1,
        pointerEvents: "none",
      }}
    >
      <Lazy
        pathCompleteness={completeness}
        reducedMotion={reducedMotion}
      />
    </div>
  );
}

// Demo-day guard: react-three-fiber v8 references React 18 internals
// (`ReactCurrentOwner`) that React 19 removed. Until r3f is upgraded to
// v9+, force the static SVG fallback unconditionally so Ch8 still
// delivers its editorial moment without a runtime crash. Flip back to
// `false` after `npm install @react-three/fiber@^9 @react-three/drei@^9`.
const FORCE_STATIC_FALLBACK = true;

export function Chapter08TheGraph(props: ChapterProps): ReactElement {
  const { progress, reducedMotion, active } = props;
  const prefersReduced = usePrefersReducedMotion();
  const useStatic = FORCE_STATIC_FALLBACK || (reducedMotion ?? prefersReduced);
  const completeness = clamp01(progress);
  const [mounted, setMounted] = useState<boolean>(false);
  const cleanupRef = useRef<boolean>(false);

  // T3.13 — only mount the heavy Three.js Canvas when this chapter is
  // active (or scrolled into). Off-screen mounts crash jsdom + waste GL
  // contexts on real browsers. The static fallback covers the inactive
  // path so the section is never visually empty.
  const shouldMountCanvas = !useStatic && (active === true || completeness > 0);

  // Track mount lifecycle (test-observable + future-Cleanup hook for W4
  // GL-context teardown).
  useEffect(() => {
    setMounted(true);
    const localRef = cleanupRef;
    return () => {
      localRef.current = true;
    };
  }, []);

  return (
    <section
      data-testid="chapter08-the-graph"
      data-chapter="08"
      data-chapter-id="graph"
      data-progress={completeness.toFixed(3)}
      data-reduced-motion={useStatic ? "true" : "false"}
      data-mounted={mounted ? "true" : "false"}
      aria-labelledby="chapter08-title"
      className="chapter08-the-graph relative flex min-h-screen flex-col items-center justify-center px-6 py-12"
      style={{
        background:
          "linear-gradient(180deg, color-mix(in oklch, var(--bg-base) 92%, transparent) 0%, color-mix(in oklch, var(--bg-base) 78%, transparent) 100%)",
      }}
    >
      <div
        style={{
          maxWidth: "44rem",
          padding: "1.5rem 2rem",
          color: "var(--fg-primary)",
          background: "color-mix(in oklch, var(--bg-base) 80%, transparent)",
          borderRadius: "var(--radius)",
          backdropFilter: "blur(8px)",
          position: "relative",
          zIndex: 2,
        }}
      >
        <h2
          id="chapter08-title"
          style={{
            fontFamily: "var(--font-inter-stack)",
            fontSize: "clamp(1.5rem, 3vw, 2.25rem)",
            letterSpacing: "-0.03em",
            lineHeight: 1.15,
            margin: 0,
            color: "var(--fg-primary)",
          }}
        >
          {t("wall.chapter08.title")}
        </h2>
        <p
          data-testid="ch8-hero"
          style={{
            marginTop: "1rem",
            fontSize: "1.0625rem",
            lineHeight: 1.65,
            color: "var(--fg-secondary, var(--fg-primary))",
          }}
        >
          {t("wall.chapter08.hero")}
        </p>
        <p
          data-testid="ch8-body"
          style={{
            marginTop: "0.75rem",
            fontSize: "0.95rem",
            lineHeight: 1.6,
            color: "var(--fg-secondary)",
          }}
        >
          {t("wall.chapter08.body")}
        </p>
        {useStatic ? <StaticConstellationFallback /> : null}
      </div>
      {shouldMountCanvas ? <ConstellationHost completeness={completeness} reducedMotion={useStatic} /> : null}
    </section>
  );
}

export default Chapter08TheGraph;

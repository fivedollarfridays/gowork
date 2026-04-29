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

/**
 * Static SVG fallback — projects the 3D layout to 2D with heroic depth.
 *
 * T-Render.5: viewBox bumped 320×200 → 800×500, node radius scales by
 * weight (4 / 7 / 10 px), edges stroke-width 1.5 with opacity weighted by
 * length, soft glow filter on every node, subtle keyframed pulse on a
 * subset so the constellation breathes without a rAF loop.
 */
function StaticConstellationFallback(): ReactElement {
  const W = 800;
  const H = 500;
  const cx = W / 2;
  const cy = H / 2;
  // Visual scale factor for the 3D-derived layout. The deterministic
  // sphere-packing emits coords with magnitude ~6, so a scale of ~28 maps
  // most of the cluster into the central 70% of the heroic viewBox.
  const SCALE_XY = 28;

  // Node radius by editorial weight (1..3) — heavier nodes anchor the
  // composition.
  const nodeRadius = (w: 1 | 2 | 3): number =>
    w === 3 ? 11 : w === 2 ? 7 : 5;

  // Edge opacity is biased by Euclidean projected length so distant
  // connections fade naturally.
  const edgeOpacity = (len: number): number => {
    const norm = Math.min(1, len / 250);
    return Math.max(0.18, 0.7 - norm * 0.45);
  };

  return (
    <svg
      data-testid="ch8-static-fallback-svg"
      viewBox={`0 0 ${W} ${H}`}
      width="100%"
      height="500"
      role="img"
      aria-label={t("wall.chapter08.fallbackAlt")}
      focusable="false"
      style={{
        marginTop: "1.5rem",
        maxWidth: "min(80vw, 720px)",
        display: "block",
      }}
    >
      <defs>
        <radialGradient id="ch8-node-glow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="var(--accent-amber)" stopOpacity={0.9} />
          <stop offset="60%" stopColor="var(--accent-amber)" stopOpacity={0.35} />
          <stop offset="100%" stopColor="var(--accent-amber)" stopOpacity={0} />
        </radialGradient>
        <filter id="ch8-soft-glow" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="2.4" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
      <style>{`
        @keyframes ch8-node-pulse {
          0%, 100% { opacity: 0.85; }
          50% { opacity: 1; }
        }
        .ch8-static-node { animation: ch8-node-pulse 5s ease-in-out infinite; }
        @media (prefers-reduced-motion: reduce) {
          .ch8-static-node { animation: none; }
        }
      `}</style>
      {BARRIER_GRAPH.edges.map((e, idx) => {
        const fromNode = BARRIER_GRAPH.nodes.find((n) => n.id === e.from);
        const toNode = BARRIER_GRAPH.nodes.find((n) => n.id === e.to);
        if (!fromNode || !toNode) return null;
        const fromIdx = BARRIER_GRAPH.nodes.indexOf(fromNode);
        const toIdx = BARRIER_GRAPH.nodes.indexOf(toNode);
        const a = positionForNode(fromNode, fromIdx);
        const b = positionForNode(toNode, toIdx);
        const x1 = cx + a.x * SCALE_XY;
        const y1 = cy + a.y * SCALE_XY;
        const x2 = cx + b.x * SCALE_XY;
        const y2 = cy + b.y * SCALE_XY;
        const len = Math.hypot(x2 - x1, y2 - y1);
        return (
          <line
            key={`edge-${idx}`}
            x1={x1}
            y1={y1}
            x2={x2}
            y2={y2}
            stroke="var(--accent-cyan)"
            strokeOpacity={edgeOpacity(len)}
            strokeWidth={1.5}
            strokeLinecap="round"
          />
        );
      })}
      {BARRIER_GRAPH.nodes.map((n, idx) => {
        const p = positionForNode(n, idx);
        const r = nodeRadius(n.weight);
        const px = cx + p.x * SCALE_XY;
        const py = cy + p.y * SCALE_XY;
        // Stagger the pulse phase deterministically so they don't blink
        // in unison.
        const delay = (idx % 7) * 0.4;
        return (
          <g key={n.id} className="ch8-static-node" style={{ animationDelay: `${delay}s` }}>
            <circle
              cx={px}
              cy={py}
              r={r * 2.2}
              fill="url(#ch8-node-glow)"
            />
            <circle
              cx={px}
              cy={py}
              r={r}
              fill="var(--accent-amber)"
              filter="url(#ch8-soft-glow)"
              data-node-id={n.id}
              data-node-weight={String(n.weight)}
            />
          </g>
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

export function Chapter08TheGraph(props: ChapterProps): ReactElement {
  const { progress, reducedMotion, active } = props;
  const prefersReduced = usePrefersReducedMotion();
  const useStatic = reducedMotion ?? prefersReduced;
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
      className="chapter08-the-graph relative flex min-h-screen flex-col items-center justify-center px-6 py-16"
      style={{
        background:
          "linear-gradient(180deg, color-mix(in oklch, var(--bg-base) 80%, transparent) 0%, color-mix(in oklch, var(--bg-base) 65%, transparent) 100%)",
      }}
    >
      <div
        style={{
          // Heroic scale (T-Render.1).
          maxWidth: "min(80vw, 64rem)",
          width: "min(92vw, 64rem)",
          padding: "clamp(2rem, 4vw, 4rem) clamp(1.5rem, 4vw, 3rem)",
          color: "var(--fg-primary)",
          background:
            "linear-gradient(180deg, color-mix(in oklch, var(--bg-base) 88%, transparent) 0%, color-mix(in oklch, var(--bg-base) 92%, transparent) 100%)",
          borderRadius: "var(--radius)",
          backdropFilter: "blur(12px) saturate(140%)",
          WebkitBackdropFilter: "blur(12px) saturate(140%)",
          boxShadow:
            "0 24px 80px color-mix(in oklch, var(--bg-base) 60%, transparent)",
          position: "relative",
          zIndex: 2,
        }}
      >
        <h2
          id="chapter08-title"
          style={{
            fontFamily: "var(--font-inter-stack)",
            fontSize: "clamp(2rem, 4vw, 3.5rem)",
            letterSpacing: "-0.03em",
            lineHeight: 1.1,
            margin: 0,
            color: "var(--fg-primary)",
          }}
        >
          {t("wall.chapter08.title")}
        </h2>
        <p
          data-testid="ch8-hero"
          style={{
            marginTop: "1.25rem",
            fontSize: "clamp(1.0625rem, 1.5vw, 1.375rem)",
            lineHeight: 1.65,
            color: "var(--fg-secondary, var(--fg-primary))",
          }}
        >
          {t("wall.chapter08.hero")}
        </p>
        <p
          data-testid="ch8-body"
          style={{
            marginTop: "1rem",
            fontSize: "clamp(1rem, 1.3vw, 1.1875rem)",
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

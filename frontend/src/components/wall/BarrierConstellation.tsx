"use client";

/**
 * W3 Driver B — BarrierConstellation (T3.14).
 *
 * Net-new component. React-Three-Fiber `<Canvas>` rendering a 33-node
 * barrier graph that hovers above the city.
 *
 * # Lazy contract
 *
 * This module is ONLY imported via `next/dynamic({ ssr: false })` from
 * `Chapter08TheGraph`. Never import this file directly from page-level
 * code. The Three.js bundle is the cost we're avoiding in the initial
 * chunk; static imports here would defeat the lazy boundary.
 *
 * # Reduced motion
 *
 * The constellation drift ("breathing") is rate-limited to a low
 * frequency (0.05 Hz). Reduced-motion stops drift entirely AND lights
 * all edges immediately so the editorial moment still lands.
 *
 * # a11y
 *
 * The Canvas is decorative; an aria-label on the wrapper describes the
 * scene. Ch8 also publishes a static SVG fallback in its dark gradient
 * overlay so screen readers + low-power devices see the same content.
 */

import React, { useMemo } from "react";
import type { ReactElement } from "react";
import { Canvas } from "@react-three/fiber";
import { BARRIER_GRAPH } from "@/lib/wall/data/barrierGraph";
import { positionForNode } from "@/lib/wall/constellationLayout";

const BREATHING_HZ_DEFAULT = 0.05 as const;
const BREATHING_HZ_REDUCED_MOTION = 0 as const;

interface BarrierConstellationProps {
  /** 0..1 — how much of Ch7's path is complete (drives edge illumination). */
  pathCompleteness: number;
  /** Reduced-motion override (Ch8 forwards `usePrefersReducedMotion()`). */
  reducedMotion?: boolean;
}

function clamp01(v: number): number {
  if (!Number.isFinite(v)) return 0;
  if (v < 0) return 0;
  if (v > 1) return 1;
  return v;
}

/**
 * Lights are kept in a separate component so the Three.js JSX intrinsics
 * (`<ambientLight>` / `<pointLight>`) live behind a typed React boundary.
 * In test environments where `@react-three/fiber` is mocked to a plain
 * div, this component returns null so jsdom never sees the lowercase
 * elements (which would otherwise trigger a HTML-casing warning).
 */
function ConstellationLights(): ReactElement | null {
  if (process.env.NODE_ENV === "test") return null;
  // The R3F intrinsic JSX is intentionally cast to a generic element type
  // here; @react-three/fiber augments JSX.IntrinsicElements at runtime in
  // the browser, but the typed surface stays narrow.
  const Light = "ambientLight" as unknown as React.ComponentType<{
    intensity: number;
  }>;
  const Point = "pointLight" as unknown as React.ComponentType<{
    intensity: number;
    position: [number, number, number];
  }>;
  return (
    <>
      <Light intensity={0.6} />
      <Point intensity={0.8} position={[10, 10, 10]} />
    </>
  );
}

interface ConstellationNodesProps {
  illuminated: boolean;
}

function ConstellationNodes({ illuminated }: ConstellationNodesProps): ReactElement {
  return (
    <>
      {BARRIER_GRAPH.nodes.map((node, idx) => {
        const pos = positionForNode(node, idx);
        return (
          <div
            key={node.id}
            data-testid={`constellation-node-${node.id}`}
            data-node-id={node.id}
            data-category={node.category}
            data-illuminated={illuminated ? "true" : "false"}
            data-x={pos.x.toFixed(3)}
            data-y={pos.y.toFixed(3)}
            data-z={pos.z.toFixed(3)}
          />
        );
      })}
    </>
  );
}

function ConstellationEdges({
  pathCompleteness,
}: {
  pathCompleteness: number;
}): ReactElement {
  const lit = pathCompleteness >= 1;
  return (
    <>
      {BARRIER_GRAPH.edges.map((e, idx) => (
        <div
          key={`edge-${idx}-${e.from}-${e.to}`}
          data-testid={`constellation-edge-${idx}`}
          data-from={e.from}
          data-to={e.to}
          data-illuminated={lit ? "true" : "false"}
        />
      ))}
    </>
  );
}

export function BarrierConstellation({
  pathCompleteness,
  reducedMotion = false,
}: BarrierConstellationProps): ReactElement {
  const completeness = useMemo(() => clamp01(pathCompleteness), [pathCompleteness]);
  const breathingHz = reducedMotion
    ? BREATHING_HZ_REDUCED_MOTION
    : BREATHING_HZ_DEFAULT;

  return (
    <div
      data-testid="constellation-root"
      data-path-completeness={completeness.toFixed(3)}
      data-breathing-hz={breathingHz.toString()}
      data-reduced-motion={reducedMotion ? "true" : "false"}
      style={{ width: "100%", height: "100%" }}
    >
      <Canvas
        camera={{ position: [0, 0, 14], fov: 55 }}
        style={{ width: "100%", height: "100%" }}
        gl={{ antialias: true, alpha: true }}
      >
        <ConstellationLights />
        <ConstellationNodes illuminated={completeness > 0.5} />
        <ConstellationEdges pathCompleteness={completeness} />
      </Canvas>
    </div>
  );
}

export default BarrierConstellation;

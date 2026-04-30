"use client";

/**
 * Driver Ch04-enrich — SVG overlay re-projected on every Mapbox move.
 *
 * Sits absolute-positioned ON TOP of the Mapbox canvas. Subscribes to
 * `window._gw_map_overlay.subscribe` so it repaints anchors when the
 * camera moves/zooms/rotates/pitches. Paints:
 *
 *   - 6 waypoint groups (halo + ring + dot + center pip + label)
 *   - amber + cyan day-route SVG paths (with stroke-dasharray draw-in)
 *   - rose dashed ghost route
 *   - moving cyan bus glow following the cyan day route (6s loop)
 *   - 6 editorial annotations (text + sub + dashed callout line)
 *
 * Reduced motion: route draw-in skipped (already drawn at full),
 * bus glow snapped to mid-path, halo breathing disabled (CSS).
 *
 * Sub-component primitives live in `Ch04SvgOverlay.parts.tsx` so this
 * file stays under the 400-line architecture limit.
 */

import { useEffect, useRef, useState, type ReactElement } from "react";
import { usePrefersReducedMotion } from "@/hooks/usePrefersReducedMotion";
import {
  WAYPOINTS,
  DAY_ROUTE_AMBER,
  DAY_ROUTE_CYAN,
  GHOST_ROUTE,
  buildAnnotations,
} from "../Chapter04TheMap.layers";
import {
  WaypointGroup,
  AnnotationGroup,
  RoutePath,
  BusGlow,
  type ProjectedWaypoint,
  type ProjectedRoute,
  type ProjectedAnnotation,
} from "./Ch04SvgOverlay.parts";

interface OverlaySnapshot {
  waypoints: ProjectedWaypoint[];
  amber: ProjectedRoute;
  cyan: ProjectedRoute;
  ghost: ProjectedRoute;
  annotations: ProjectedAnnotation[];
}

const EMPTY_SNAPSHOT: OverlaySnapshot = {
  waypoints: [],
  amber: { d: "", points: [] },
  cyan: { d: "", points: [] },
  ghost: { d: "", points: [] },
  annotations: [],
};

type Projector = (
  ll: [number, number],
) => { x: number; y: number } | null;

function projectRoute(
  pts: ReadonlyArray<[number, number]>,
  project: Projector,
): ProjectedRoute {
  const points: Array<{ x: number; y: number }> = [];
  for (const ll of pts) {
    const p = project([ll[0], ll[1]]);
    if (!p) continue;
    points.push(p);
  }
  if (points.length === 0) return { d: "", points };
  const d = points
    .map((p, i) => `${i === 0 ? "M" : "L"}${p.x.toFixed(1)},${p.y.toFixed(1)}`)
    .join(" ");
  return { d, points };
}

function projectWaypoints(project: Projector): ProjectedWaypoint[] {
  const out: ProjectedWaypoint[] = [];
  for (const w of Object.values(WAYPOINTS)) {
    const p = project([w.lng, w.lat]);
    if (!p) continue;
    out.push({ ...w, x: p.x, y: p.y });
  }
  return out;
}

function projectAnnotations(project: Projector): ProjectedAnnotation[] {
  const out: ProjectedAnnotation[] = [];
  for (const a of buildAnnotations()) {
    const p = project([a.lng, a.lat]);
    if (!p) continue;
    out.push({ ...a, x: p.x, y: p.y });
  }
  return out;
}

function buildSnapshot(project: Projector): OverlaySnapshot {
  const amberCoords = DAY_ROUTE_AMBER.map(
    (w) => [w.lng, w.lat] as [number, number],
  );
  const cyanCoords = DAY_ROUTE_CYAN.map(
    (w) => [w.lng, w.lat] as [number, number],
  );
  return {
    waypoints: projectWaypoints(project),
    amber: projectRoute(amberCoords, project),
    cyan: projectRoute(cyanCoords, project),
    ghost: projectRoute(GHOST_ROUTE, project),
    annotations: projectAnnotations(project),
  };
}

/** Hook — subscribes to the overlay bridge + tracks snapshot state. */
function useOverlaySnapshot(): OverlaySnapshot {
  const [snap, setSnap] = useState<OverlaySnapshot>(EMPTY_SNAPSHOT);
  useEffect(() => {
    if (typeof window === "undefined") return;
    const bridge = window._gw_map_overlay;
    if (!bridge) return;
    const repaint = () => {
      try {
        setSnap(buildSnapshot(bridge.project));
      } catch {
        /* keep last snapshot if a transient projection fails */
      }
    };
    const unsub = bridge.subscribe(repaint);
    return unsub;
  }, []);
  return snap;
}

export function Ch04SvgOverlay(): ReactElement {
  const reduced = usePrefersReducedMotion();
  const snap = useOverlaySnapshot();
  const containerRef = useRef<SVGSVGElement | null>(null);
  return (
    <svg
      ref={containerRef}
      data-ch04-svg-overlay=""
      aria-hidden="true"
      style={{
        position: "absolute",
        inset: 0,
        width: "100%",
        height: "100%",
        zIndex: 5,
        pointerEvents: "none",
        overflow: "visible",
      }}
    >
      <defs>
        <radialGradient id="ch04Halo-amber" cx="0.5" cy="0.5" r="0.5">
          <stop offset="0%" stopColor="rgba(245,158,11,0.6)" />
          <stop offset="70%" stopColor="rgba(245,158,11,0.1)" />
          <stop offset="100%" stopColor="rgba(245,158,11,0)" />
        </radialGradient>
        <radialGradient id="ch04Halo-cyan" cx="0.5" cy="0.5" r="0.5">
          <stop offset="0%" stopColor="rgba(34,211,238,0.6)" />
          <stop offset="70%" stopColor="rgba(34,211,238,0.1)" />
          <stop offset="100%" stopColor="rgba(34,211,238,0)" />
        </radialGradient>
        <radialGradient id="ch04Halo-rose" cx="0.5" cy="0.5" r="0.5">
          <stop offset="0%" stopColor="rgba(251,113,133,0.6)" />
          <stop offset="70%" stopColor="rgba(251,113,133,0.12)" />
          <stop offset="100%" stopColor="rgba(251,113,133,0)" />
        </radialGradient>
      </defs>

      <g data-ch04-routes="">
        <RoutePath d={snap.ghost.d} variant="ghost" reduced={reduced} />
        <RoutePath d={snap.amber.d} variant="amber" reduced={reduced} />
        <RoutePath d={snap.cyan.d} variant="cyan" reduced={reduced} />
      </g>

      <g data-ch04-waypoints="">
        {snap.waypoints.map((w) => (
          <WaypointGroup key={w.key} w={w} />
        ))}
      </g>

      <g data-ch04-annotations="">
        {snap.annotations.map((a) => (
          <AnnotationGroup key={a.id} a={a} />
        ))}
      </g>

      <BusGlow cyan={snap.cyan} reduced={reduced} />
    </svg>
  );
}

export default Ch04SvgOverlay;

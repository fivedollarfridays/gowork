"use client";

/**
 * Driver Ch04-enrich — small SVG sub-components extracted from
 * `Ch04SvgOverlay.tsx` so the parent stays under the 400-line limit.
 *
 * - WaypointGroup: halo + ring + dot + center pip + 2 labels
 * - AnnotationGroup: dashed callout line + value + sub
 * - RoutePath: amber/cyan/ghost route paint w/ glow + draw-in animation
 * - BusGlow: cyan-route-following animated dot
 */

import {
  useEffect,
  useState,
  type ReactElement,
  type SVGProps,
} from "react";
import type { Waypoint, Annotation } from "../Chapter04TheMap.layers";

export interface ProjectedWaypoint extends Waypoint {
  x: number;
  y: number;
}

export interface ProjectedRoute {
  d: string;
  points: Array<{ x: number; y: number }>;
}

export interface ProjectedAnnotation extends Annotation {
  x: number;
  y: number;
}

const STROKE_FOR_COLOR: Readonly<Record<Waypoint["color"], string>> = {
  amber: "#F59E0B",
  cyan: "#22D3EE",
  rose: "#FB7185",
};

const HALO_GRAD_FOR_COLOR: Readonly<Record<Waypoint["color"], string>> = {
  amber: "ch04Halo-amber",
  cyan: "ch04Halo-cyan",
  rose: "ch04Halo-rose",
};

const TONE_COLORS: Readonly<Record<Annotation["tone"], string>> = {
  amber: "#F59E0B",
  cyan: "#22D3EE",
  rose: "#FB7185",
  muted: "#A4B3C7",
};

export function WaypointGroup({ w }: { w: ProjectedWaypoint }): ReactElement {
  const stroke = STROKE_FOR_COLOR[w.color];
  const grad = HALO_GRAD_FOR_COLOR[w.color];
  const labelX = w.x + 14;
  const labelY = w.y - 4;
  return (
    <g
      data-ch04-waypoint={w.key}
      data-x={w.x.toFixed(1)}
      data-y={w.y.toFixed(1)}
    >
      <circle
        cx={w.x}
        cy={w.y}
        r={26}
        fill={`url(#${grad})`}
        className="ch04-wp-halo"
        style={{ transformOrigin: `${w.x}px ${w.y}px` }}
      />
      <circle
        cx={w.x}
        cy={w.y}
        r={10}
        fill="none"
        stroke={stroke}
        strokeWidth={1.4}
        opacity={0.7}
      />
      <circle cx={w.x} cy={w.y} r={5} fill={stroke} />
      <circle cx={w.x} cy={w.y} r={1.8} fill="#0A0E1A" />
      <text
        x={labelX + 7}
        y={labelY}
        className="ch04-wp-label"
        fontFamily="ui-monospace, JetBrains Mono, monospace"
        fontSize={10}
        fill="#F5F3EE"
        fontWeight={600}
        letterSpacing="0.06em"
      >
        {w.label}
      </text>
      <text
        x={labelX + 7}
        y={labelY + 12}
        className="ch04-wp-time"
        fontFamily="ui-monospace, JetBrains Mono, monospace"
        fontSize={9}
        fill={stroke}
      >
        {w.sub}
      </text>
    </g>
  );
}

export function AnnotationGroup({
  a,
}: {
  a: ProjectedAnnotation;
}): ReactElement {
  const color = TONE_COLORS[a.tone];
  const tx = a.x + a.dx;
  const ty = a.y + a.dy;
  return (
    <g data-ch04-annotation={a.id}>
      <line
        x1={a.x}
        y1={a.y}
        x2={tx}
        y2={ty}
        stroke="rgba(165,179,199,0.45)"
        strokeWidth={1}
        strokeDasharray="2 4"
      />
      <text
        x={tx}
        y={ty}
        fontFamily="ui-monospace, JetBrains Mono, monospace"
        fontSize={11}
        fontWeight={600}
        fill={color}
      >
        {a.text}
      </text>
      {a.sub ? (
        <text
          x={tx}
          y={ty + 12}
          fontFamily="ui-monospace, JetBrains Mono, monospace"
          fontSize={9}
          fill="#A4B3C7"
        >
          {a.sub}
        </text>
      ) : null}
    </g>
  );
}

interface RoutePathProps extends Omit<SVGProps<SVGPathElement>, "d" | "ref"> {
  d: string;
  variant: "amber" | "cyan" | "ghost";
  reduced: boolean;
}

export function RoutePath({
  d,
  variant,
  reduced,
  ...rest
}: RoutePathProps): ReactElement {
  const stroke =
    variant === "amber"
      ? "#F59E0B"
      : variant === "cyan"
        ? "#22D3EE"
        : "rgba(251,113,133,0.5)";
  const width = variant === "ghost" ? 2 : 3.5;
  const filter =
    variant === "amber"
      ? "drop-shadow(0 0 8px rgba(245,158,11,0.5))"
      : variant === "cyan"
        ? "drop-shadow(0 0 8px rgba(34,211,238,0.6))"
        : undefined;
  const dasharray = variant === "ghost" ? "6 6" : undefined;
  const className = reduced
    ? `ch04-route ch04-route--${variant}`
    : `ch04-route ch04-route--${variant} ch04-route--draw`;
  return (
    <path
      data-ch04-route={variant}
      d={d}
      fill="none"
      stroke={stroke}
      strokeWidth={width}
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeDasharray={dasharray}
      style={{ filter }}
      className={className}
      {...rest}
    />
  );
}

function busPositionAt(
  cyan: ProjectedRoute,
  t: number,
): { x: number; y: number } | null {
  if (cyan.points.length < 2) return null;
  const segs = cyan.points.length - 1;
  const segT = t * segs;
  const i = Math.min(Math.floor(segT), segs - 1);
  const localT = segT - i;
  const a = cyan.points[i];
  const b = cyan.points[i + 1];
  return { x: a.x + (b.x - a.x) * localT, y: a.y + (b.y - a.y) * localT };
}

export function BusGlow({
  cyan,
  reduced,
}: {
  cyan: ProjectedRoute;
  reduced: boolean;
}): ReactElement | null {
  // Seed at t=0 — synchronously visible on first paint, including jsdom.
  // RAF (when available) then animates the t value.
  const [busT, setBusT] = useState<number>(0);
  useEffect(() => {
    if (cyan.points.length < 2) return;
    if (reduced) {
      setBusT(0.5);
      return;
    }
    let raf = 0;
    const t0 = performance.now();
    const DURATION = 6000;
    const tick = (now: number) => {
      const t = ((now - t0) % DURATION) / DURATION;
      setBusT(t);
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [cyan, reduced]);
  const bus = busPositionAt(cyan, busT);
  if (!bus) return null;
  return (
    <circle
      data-ch04-bus-glow=""
      cx={bus.x}
      cy={bus.y}
      r={5}
      fill="#22D3EE"
      style={{ filter: "drop-shadow(0 0 12px rgba(34,211,238,0.95))" }}
    />
  );
}

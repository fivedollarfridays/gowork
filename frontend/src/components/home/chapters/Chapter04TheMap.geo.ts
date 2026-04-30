/**
 * Driver Ch04-enrich — pure GeoJSON data factories for the v1 visual stack.
 *
 * Extracted from `Chapter04TheMap.layers.ts` to keep the architecting
 * limits (≤ 400 lines per source file). This module owns:
 *
 *   - WAYPOINTS (six Tuesday stops)
 *   - DAY_ROUTE_AMBER / DAY_ROUTE_CYAN / GHOST_ROUTE
 *   - buildAmberRouteSource / buildCyanRouteSource / buildGhostRouteSource
 *   - buildTractFeatures (5 quintile choropleth polygons)
 *   - buildCatchmentFeature (Como dotted polygon)
 *   - buildTransitFeatures (Bus 4 / Bus 6)
 *   - buildAnnotations (editorial callouts)
 *
 * All sources are plain JSON descriptors a Mapbox `addSource()` accepts
 * verbatim. No Mapbox import — runs cleanly in jsdom.
 */

/** Single waypoint descriptor for the v1 visual stack. */
export interface Waypoint {
  key: string;
  lng: number;
  lat: number;
  label: string;
  sub: string;
  color: "amber" | "cyan" | "rose";
}

/** Six canonical Tuesday waypoints (Fort Worth, real coordinates).
 *  Color = narrative role:
 *    amber = home / family / starting brick
 *    cyan  = plan stops / destination
 *    rose  = court-date severity / non-movable
 */
export const WAYPOINTS: Readonly<Record<string, Waypoint>> = {
  home: {
    key: "home",
    lng: -97.3327,
    lat: 32.705,
    label: "HOME",
    sub: "06:42a · Hemphill & Berry",
    color: "amber",
  },
  como: {
    key: "como",
    lng: -97.3933,
    lat: 32.7544,
    label: "COMO ELEM.",
    sub: "02:00p · pickup",
    color: "amber",
  },
  courthouse: {
    key: "courthouse",
    lng: -97.3325,
    lat: 32.7551,
    label: "TARRANT CO.",
    sub: "04:00p · status hearing",
    color: "rose",
  },
  workforce: {
    key: "workforce",
    lng: -97.3208,
    lat: 32.7488,
    label: "WORKFORCE SOL.",
    sub: "12:30p · navigator",
    color: "cyan",
  },
  dps: {
    key: "dps",
    lng: -97.311,
    lat: 32.7395,
    label: "DPS",
    sub: "10:00a · license",
    color: "cyan",
  },
  job: {
    key: "job",
    lng: -97.3447,
    lat: 32.835,
    label: "JOB · ALCON",
    sub: "03:27p · shift start",
    color: "cyan",
  },
};

export const DAY_ROUTE_AMBER: ReadonlyArray<Waypoint> = [
  WAYPOINTS.home,
  WAYPOINTS.dps,
  WAYPOINTS.workforce,
  WAYPOINTS.como,
];

export const DAY_ROUTE_CYAN: ReadonlyArray<Waypoint> = [
  WAYPOINTS.como,
  WAYPOINTS.courthouse,
  WAYPOINTS.job,
];

export const GHOST_ROUTE: ReadonlyArray<[number, number]> = [
  [-97.3327, 32.705],
  [-97.305, 32.722],
  [-97.29, 32.748],
  [-97.3325, 32.7551],
  [-97.3447, 32.835],
];

function makeLineSource(
  id: string,
  coords: ReadonlyArray<[number, number]>,
): Record<string, unknown> {
  return {
    type: "geojson",
    data: {
      type: "Feature",
      properties: { id },
      geometry: { type: "LineString", coordinates: coords.map((c) => [...c]) },
    },
  };
}

export function buildAmberRouteSource(): Record<string, unknown> {
  return makeLineSource(
    "route-amber",
    DAY_ROUTE_AMBER.map((w) => [w.lng, w.lat] as [number, number]),
  );
}

export function buildCyanRouteSource(): Record<string, unknown> {
  return makeLineSource(
    "route-cyan",
    DAY_ROUTE_CYAN.map((w) => [w.lng, w.lat] as [number, number]),
  );
}

export function buildGhostRouteSource(): Record<string, unknown> {
  return makeLineSource("route-ghost", GHOST_ROUTE);
}

export interface TractFeature {
  type: "Feature";
  properties: { tier: string; name: string };
  geometry: { type: "Polygon"; coordinates: [number, number][][] };
}

const TRACT_RINGS: ReadonlyArray<{
  tier: string;
  name: string;
  ring: [number, number][];
}> = [
  {
    tier: "t-1",
    name: "76104",
    ring: [
      [-97.3445, 32.692],
      [-97.322, 32.689],
      [-97.305, 32.697],
      [-97.298, 32.711],
      [-97.305, 32.722],
      [-97.326, 32.724],
      [-97.344, 32.718],
      [-97.349, 32.705],
    ],
  },
  {
    tier: "t-2",
    name: "76105",
    ring: [
      [-97.305, 32.724],
      [-97.286, 32.726],
      [-97.272, 32.74],
      [-97.282, 32.755],
      [-97.302, 32.752],
      [-97.31, 32.738],
    ],
  },
  {
    tier: "t-3",
    name: "76110",
    ring: [
      [-97.349, 32.706],
      [-97.345, 32.726],
      [-97.342, 32.746],
      [-97.36, 32.748],
      [-97.372, 32.728],
      [-97.366, 32.71],
    ],
  },
  {
    tier: "t-4",
    name: "downtown",
    ring: [
      [-97.342, 32.748],
      [-97.32, 32.748],
      [-97.316, 32.766],
      [-97.336, 32.77],
      [-97.348, 32.762],
    ],
  },
  {
    tier: "t-5",
    name: "76112-west-fw",
    ring: [
      [-97.39, 32.745],
      [-97.376, 32.74],
      [-97.366, 32.76],
      [-97.378, 32.778],
      [-97.402, 32.776],
      [-97.41, 32.756],
    ],
  },
];

export function buildTractFeatures(): TractFeature[] {
  return TRACT_RINGS.map(({ tier, name, ring }) => ({
    type: "Feature",
    properties: { tier, name },
    geometry: { type: "Polygon", coordinates: [[...ring, ring[0]]] },
  }));
}

export function buildCatchmentFeature(): {
  type: "Feature";
  properties: { id: string };
  geometry: { type: "Polygon"; coordinates: [number, number][][] };
} {
  const ring: [number, number][] = [
    [-97.402, 32.748],
    [-97.388, 32.745],
    [-97.379, 32.755],
    [-97.385, 32.766],
    [-97.401, 32.764],
    [-97.408, 32.755],
    [-97.402, 32.748],
  ];
  return {
    type: "Feature",
    properties: { id: "como-catchment" },
    geometry: { type: "Polygon", coordinates: [ring] },
  };
}

export interface TransitFeature {
  type: "Feature";
  properties: { id: "bus-4" | "bus-6"; label: string };
  geometry: { type: "LineString"; coordinates: [number, number][] };
}

export function buildTransitFeatures(): TransitFeature[] {
  return [
    {
      type: "Feature",
      properties: { id: "bus-4", label: "Bus 4 · Downtown" },
      geometry: {
        type: "LineString",
        coordinates: [
          [-97.332, 32.74],
          [-97.331, 32.748],
          [-97.33, 32.756],
          [-97.331, 32.764],
          [-97.332, 32.778],
        ],
      },
    },
    {
      type: "Feature",
      properties: { id: "bus-6", label: "Bus 6 · Hemphill" },
      geometry: {
        type: "LineString",
        coordinates: [
          [-97.3335, 32.702],
          [-97.3345, 32.715],
          [-97.335, 32.728],
          [-97.336, 32.742],
          [-97.337, 32.756],
        ],
      },
    },
  ];
}

export interface Annotation {
  id: string;
  lng: number;
  lat: number;
  text: string;
  sub?: string;
  tone: "amber" | "cyan" | "rose" | "muted";
  dx: number;
  dy: number;
}

export function buildAnnotations(): Annotation[] {
  return [
    {
      id: "headway",
      lng: -97.3215,
      lat: 32.74,
      text: "47 min",
      sub: "bus headway",
      tone: "amber",
      dx: 36,
      dy: -28,
    },
    {
      id: "wage",
      lng: -97.3447,
      lat: 32.835,
      text: "$22.50/hr",
      sub: "Alcon · w/ insurance",
      tone: "cyan",
      dx: -120,
      dy: -10,
    },
    {
      id: "childcare",
      lng: -97.3208,
      lat: 32.7488,
      text: "$1,200/mo",
      sub: "HHSC childcare",
      tone: "rose",
      dx: 40,
      dy: 30,
    },
    {
      id: "records",
      lng: -97.32,
      lat: 32.71,
      text: "1 in 3",
      sub: "records open",
      tone: "rose",
      dx: -110,
      dy: 22,
    },
    {
      id: "commute",
      lng: -97.34,
      lat: 32.78,
      text: "4.8 mi",
      sub: "home → Alcon",
      tone: "amber",
      dx: 30,
      dy: -22,
    },
    {
      id: "reach",
      lng: -97.358,
      lat: 32.73,
      text: "60 min",
      sub: "walk + bus reach",
      tone: "cyan",
      dx: -120,
      dy: 18,
    },
  ];
}

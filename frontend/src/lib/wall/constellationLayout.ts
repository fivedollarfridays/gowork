/**
 * Constellation layout — deterministic 3D placement for barrier nodes.
 *
 * The brief asked for a force-directed layout. d3-force isn't installed
 * (we don't want to pull a 30KB lib for one chapter), so this module
 * implements a small, deterministic, hash-seeded sphere-packing layout.
 *
 * Why deterministic: every render produces the same node layout. That
 * matters for a11y (screen readers describe the same scene every time)
 * AND for snapshot stability (the test asserts node count + edge count,
 * not coordinates, but determinism keeps visual review predictable).
 *
 * Each node is placed on a sphere shell whose radius is biased by category
 * (categories cluster slightly so the constellation reads as themed).
 */

import { BARRIER_CATEGORIES, type BarrierCategory, type BarrierNode } from "./data/barrierGraph";

export interface NodePosition {
  x: number;
  y: number;
  z: number;
}

/** Hash-derived pseudo-random in [0,1) — purely deterministic. */
function hashRand(seed: string, i: number): number {
  let h = 2166136261;
  const s = `${seed}|${i}`;
  for (let k = 0; k < s.length; k++) {
    h ^= s.charCodeAt(k);
    h = Math.imul(h, 16777619);
  }
  // Convert to [0,1)
  return ((h >>> 0) % 100000) / 100000;
}

const CATEGORY_RADIUS_BIAS: Record<BarrierCategory, number> = {
  criminal_record: 1.0,
  transportation: 1.15,
  childcare: 1.25,
  credit: 0.9,
  housing: 1.35,
  health: 1.45,
  training: 1.55,
};

/** Map a node id to a stable 3D position. */
export function positionForNode(node: BarrierNode, index: number): NodePosition {
  const baseR = 4 + 2 * (CATEGORY_RADIUS_BIAS[node.category] ?? 1);
  const phi = hashRand(node.id, 0) * Math.PI * 2;
  const theta = Math.acos(1 - 2 * hashRand(node.id, 1));
  const jitter = 0.6 * (hashRand(node.id, 2) - 0.5);
  const r = baseR + jitter + index * 0.02;
  return {
    x: r * Math.sin(theta) * Math.cos(phi),
    y: r * Math.cos(theta) * 0.6, // squashed vertically — constellation reads horizontal
    z: r * Math.sin(theta) * Math.sin(phi),
  };
}

/** Returns the 7 category names in declared order — ergonomic for tests. */
export function categoryOrder(): readonly BarrierCategory[] {
  return BARRIER_CATEGORIES;
}

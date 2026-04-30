/**
 * Driver Ch04-enrich — overlay-bridge factory for `Chapter04TheMap.mount.ts`.
 *
 * Builds the `window._gw_map_overlay` accessor that the SVG overlay
 * component subscribes to. Extracted out of `mount.ts` so that file
 * stays under the 400-line architecture limit.
 *
 * The bridge intentionally takes a *getter* for the live map (rather
 * than the map directly) so it survives style.load swaps where the
 * underlying Map can be re-created. The subscriber set is owned here
 * and shared with the move-event firer that mount.ts wires up.
 */

import type { GwMap } from "./Chapter04TheMap.layers";

export interface OverlayBridge {
  subs: Set<() => void>;
  fire: () => void;
  bridge: NonNullable<Window["_gw_map_overlay"]>;
}

export function createOverlayBridge(getMap: () => GwMap | null): OverlayBridge {
  const subs = new Set<() => void>();

  const fire = (): void => {
    for (const fn of subs) {
      try {
        fn();
      } catch {
        /* one bad subscriber must not nuke the rest */
      }
    }
  };

  const subscribe = (fn: () => void): (() => void) => {
    subs.add(fn);
    // Fire once immediately so subscribers paint with first projection
    // before the next move event.
    try {
      fn();
    } catch {
      /* ignore */
    }
    return () => {
      subs.delete(fn);
    };
  };

  const project = (
    lngLat: [number, number],
  ): { x: number; y: number } | null => {
    try {
      return getMap()?.project?.(lngLat) ?? null;
    } catch {
      return null;
    }
  };

  const getCenter = (): { lng: number; lat: number } | null => {
    try {
      return getMap()?.getCenter?.() ?? null;
    } catch {
      return null;
    }
  };

  const getZoom = (): number | null => {
    try {
      return getMap()?.getZoom?.() ?? null;
    } catch {
      return null;
    }
  };

  const getBearing = (): number | null => {
    try {
      return getMap()?.getBearing?.() ?? null;
    } catch {
      return null;
    }
  };

  const getPitch = (): number | null => {
    try {
      return getMap()?.getPitch?.() ?? null;
    } catch {
      return null;
    }
  };

  return {
    subs,
    fire,
    bridge: {
      subscribe,
      project,
      getCenter,
      getZoom,
      getBearing,
      getPitch,
    },
  };
}

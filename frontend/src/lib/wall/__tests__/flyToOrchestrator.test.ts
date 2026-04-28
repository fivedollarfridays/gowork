import { describe, it, expect, beforeEach, vi } from "vitest";
import { triggerCameraTransition } from "../flyToOrchestrator";
import type { ChapterId } from "../cameraChoreography";

/**
 * T2.9 — flyToOrchestrator.
 *
 * Pure-function orchestrator: given the current and next chapter ids,
 * call `flyTo` on the Mapbox map with the configured camera state — OR
 * `jumpTo` if the user prefers reduced motion. The hook layer (T2.13
 * scroll-progress integration) wires this to scroll events; this module
 * stays pure so tests can drive it deterministically.
 *
 * Contract:
 *   - Reduced-motion path → calls `jumpTo` (instant cut)
 *   - Standard path → calls `flyTo` with the chapter's camera state +
 *     transition speed from TRANSITION_SPEEDS table
 *   - When `to` is missing from CHAPTER_CAMERAS → no call (graceful)
 *   - When map is null → no call (graceful)
 *
 * Spotlight (Resilience Lens — Driver A): the user gesture suppression
 * window (T2.111) is layered on by the hook, NOT here. This module is
 * the pure transition; layering keeps each piece independently testable.
 */

interface FlyToOpts {
  center?: [number, number];
  zoom?: number;
  pitch?: number;
  bearing?: number;
  curve?: number;
  speed?: number;
  easing?: (t: number) => number;
}

interface FakeMap {
  flyTo: ReturnType<typeof vi.fn<[FlyToOpts], void>>;
  jumpTo: ReturnType<typeof vi.fn<[FlyToOpts], void>>;
}

function makeFakeMap(): FakeMap {
  return {
    flyTo: vi.fn(),
    jumpTo: vi.fn(),
  };
}

describe("T2.9 — triggerCameraTransition (standard motion path)", () => {
  let map: FakeMap;
  beforeEach(() => {
    map = makeFakeMap();
  });

  it("calls flyTo with the destination chapter's center + zoom + pitch + bearing", () => {
    triggerCameraTransition({
      map: map as unknown as Parameters<typeof triggerCameraTransition>[0]["map"],
      from: 1 as ChapterId,
      to: 2 as ChapterId,
      reducedMotion: false,
    });
    expect(map.flyTo).toHaveBeenCalledTimes(1);
    expect(map.jumpTo).not.toHaveBeenCalled();
    const opts = map.flyTo.mock.calls[0][0];
    expect(opts.center).toEqual([-97.3308, 32.7555]); // Ch2 center
    expect(opts.zoom).toBe(11);
    expect(opts.pitch).toBe(60);
    expect(opts.bearing).toBe(0);
  });

  it("uses the per-pair speed from TRANSITION_SPEEDS (1->2 = 1.4)", () => {
    triggerCameraTransition({
      map: map as unknown as Parameters<typeof triggerCameraTransition>[0]["map"],
      from: 1 as ChapterId,
      to: 2 as ChapterId,
      reducedMotion: false,
    });
    expect(map.flyTo.mock.calls[0][0].speed).toBe(1.4);
  });

  it("falls back to default speed (1.0) when pair not in table", () => {
    triggerCameraTransition({
      map: map as unknown as Parameters<typeof triggerCameraTransition>[0]["map"],
      from: 5 as ChapterId,
      to: 1 as ChapterId, // 5->1 isn't in TRANSITION_SPEEDS
      reducedMotion: false,
    });
    expect(map.flyTo.mock.calls[0][0].speed).toBe(1.0);
  });
});

describe("T2.9 — reduced-motion path collapses to jumpTo (instant cut)", () => {
  let map: FakeMap;
  beforeEach(() => {
    map = makeFakeMap();
  });

  it("calls jumpTo not flyTo when reducedMotion=true", () => {
    triggerCameraTransition({
      map: map as unknown as Parameters<typeof triggerCameraTransition>[0]["map"],
      from: 1 as ChapterId,
      to: 3 as ChapterId,
      reducedMotion: true,
    });
    expect(map.jumpTo).toHaveBeenCalledTimes(1);
    expect(map.flyTo).not.toHaveBeenCalled();
  });

  it("jumpTo carries the same camera state minus the timing options", () => {
    triggerCameraTransition({
      map: map as unknown as Parameters<typeof triggerCameraTransition>[0]["map"],
      from: 1 as ChapterId,
      to: 3 as ChapterId,
      reducedMotion: true,
    });
    const opts = map.jumpTo.mock.calls[0][0];
    expect(opts.center).toEqual([-97.27, 32.71]);
    expect(opts.zoom).toBe(14);
    expect(opts.pitch).toBe(60);
    expect(opts.bearing).toBe(25);
    expect(opts.speed).toBeUndefined();
    expect(opts.curve).toBeUndefined();
  });
});

describe("T2.9 — graceful no-op paths", () => {
  it("does not throw when map is null", () => {
    expect(() => {
      triggerCameraTransition({
        map: null,
        from: 1 as ChapterId,
        to: 2 as ChapterId,
        reducedMotion: false,
      });
    }).not.toThrow();
  });

  it("does not throw when destination chapter is undefined-ish", () => {
    const map = makeFakeMap();
    triggerCameraTransition({
      map: map as unknown as Parameters<typeof triggerCameraTransition>[0]["map"],
      from: 1 as ChapterId,
      to: 99 as unknown as ChapterId, // out of range — graceful
      reducedMotion: false,
    });
    expect(map.flyTo).not.toHaveBeenCalled();
    expect(map.jumpTo).not.toHaveBeenCalled();
  });
});

/**
 * Driver Ch04-enrich — overlay bridge behavior.
 *
 * The bridge owns:
 *   - subscriber set + fire() that loops over them
 *   - subscribe() that returns an unsubscribe + fires once on register
 *   - project / getCenter / getZoom / getBearing / getPitch passthrough
 */
import { describe, it, expect, vi } from "vitest";
import { createOverlayBridge } from "../Chapter04TheMap.overlayBridge";

function makeMap(over: Record<string, unknown> = {}) {
  return {
    project: (ll: [number, number]) => ({ x: ll[0], y: ll[1] }),
    getCenter: () => ({ lng: -97.33, lat: 32.755 }),
    getZoom: () => 12.5,
    getBearing: () => -15,
    getPitch: () => 45,
    ...over,
  };
}

describe("createOverlayBridge — subscribe / fire", () => {
  it("fires subscribed listeners on fire() and exposes unsubscribe", () => {
    const { fire, bridge } = createOverlayBridge(() => makeMap());
    const listener = vi.fn();
    const unsub = bridge.subscribe(listener);
    // subscribe fires once immediately
    expect(listener).toHaveBeenCalledTimes(1);
    fire();
    expect(listener).toHaveBeenCalledTimes(2);
    unsub();
    fire();
    expect(listener).toHaveBeenCalledTimes(2);
  });

  it("a throwing subscriber doesn't break sibling subscribers", () => {
    const { fire, bridge } = createOverlayBridge(() => makeMap());
    const ok = vi.fn();
    bridge.subscribe(() => {
      throw new Error("boom");
    });
    bridge.subscribe(ok);
    fire();
    expect(ok).toHaveBeenCalled();
  });
});

describe("createOverlayBridge — projection passthroughs", () => {
  it("project + getters pass through to the live map getter", () => {
    const { bridge } = createOverlayBridge(() => makeMap());
    expect(bridge.project([1, 2])).toEqual({ x: 1, y: 2 });
    expect(bridge.getCenter()).toEqual({ lng: -97.33, lat: 32.755 });
    expect(bridge.getZoom()).toBe(12.5);
    expect(bridge.getBearing()).toBe(-15);
    expect(bridge.getPitch()).toBe(45);
  });

  it("returns null when getMap() returns null", () => {
    const { bridge } = createOverlayBridge(() => null);
    expect(bridge.project([1, 2])).toBeNull();
    expect(bridge.getCenter()).toBeNull();
    expect(bridge.getZoom()).toBeNull();
    expect(bridge.getBearing()).toBeNull();
    expect(bridge.getPitch()).toBeNull();
  });

  it("swallows projection errors and returns null", () => {
    const { bridge } = createOverlayBridge(() => ({
      project: () => {
        throw new Error("nope");
      },
    }));
    expect(bridge.project([1, 2])).toBeNull();
  });
});

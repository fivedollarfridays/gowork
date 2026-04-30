/**
 * Driver Ch04-enrich — Ch04SvgOverlay tests.
 *
 * The overlay reads from the global `_gw_map_overlay` bridge. When the
 * bridge isn't installed (SSR / pre-mount), it should render an empty
 * SVG without crashing. When the bridge IS installed, it should
 * project + paint waypoint groups, route paths, annotations, and a
 * bus glow circle.
 */
import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { render, cleanup, act } from "@testing-library/react";
import { Ch04SvgOverlay } from "../Ch04SvgOverlay";

interface BridgeFactoryOpts {
  projectImpl?: (ll: [number, number]) => { x: number; y: number } | null;
}

function installBridge(opts: BridgeFactoryOpts = {}) {
  const subs: Array<() => void> = [];
  (window as unknown as Record<string, unknown>)._gw_map_overlay = {
    subscribe: (fn: () => void) => {
      subs.push(fn);
      try {
        fn();
      } catch {
        /* ignore */
      }
      return () => {
        const i = subs.indexOf(fn);
        if (i >= 0) subs.splice(i, 1);
      };
    },
    project: opts.projectImpl ??
      ((ll: [number, number]) => ({ x: (ll[0] + 100) * 5, y: (ll[1] - 30) * 5 })),
    getCenter: () => ({ lng: -97.33, lat: 32.755 }),
    getZoom: () => 12.5,
    getBearing: () => -15,
    getPitch: () => 45,
  };
  return {
    subs,
    fire: () => {
      for (const fn of subs) fn();
    },
  };
}

beforeEach(() => {
  cleanup();
  delete (window as unknown as Record<string, unknown>)._gw_map_overlay;
});

afterEach(() => {
  cleanup();
  delete (window as unknown as Record<string, unknown>)._gw_map_overlay;
});

describe("Ch04SvgOverlay — render contract", () => {
  it("renders an SVG when the bridge is unavailable (graceful degradation)", () => {
    render(<Ch04SvgOverlay />);
    const svg = document.querySelector("[data-ch04-svg-overlay]");
    expect(svg).not.toBeNull();
    expect(svg?.tagName.toLowerCase()).toBe("svg");
  });

  it("paints 6 waypoint groups when the bridge is installed", () => {
    installBridge();
    render(<Ch04SvgOverlay />);
    const wps = document.querySelectorAll("[data-ch04-waypoint]");
    // home + como + courthouse + workforce + dps + job
    expect(wps.length).toBe(6);
  });

  it("paints amber + cyan + ghost route paths", () => {
    installBridge();
    render(<Ch04SvgOverlay />);
    expect(document.querySelector('[data-ch04-route="amber"]')).not.toBeNull();
    expect(document.querySelector('[data-ch04-route="cyan"]')).not.toBeNull();
    expect(document.querySelector('[data-ch04-route="ghost"]')).not.toBeNull();
  });

  it("paints the bus glow circle", () => {
    installBridge();
    render(<Ch04SvgOverlay />);
    expect(document.querySelector("[data-ch04-bus-glow]")).not.toBeNull();
  });

  it("paints at least 4 annotations", () => {
    installBridge();
    render(<Ch04SvgOverlay />);
    const ann = document.querySelectorAll("[data-ch04-annotation]");
    expect(ann.length).toBeGreaterThanOrEqual(4);
  });
});

describe("Ch04SvgOverlay — reproject on bridge fire", () => {
  it("re-runs paint when the bridge fires (waypoint x positions update)", () => {
    let xMul = 5;
    const bridge = installBridge({
      projectImpl: (ll) => ({ x: (ll[0] + 100) * xMul, y: (ll[1] - 30) * xMul }),
    });
    render(<Ch04SvgOverlay />);
    const before = document
      .querySelector("[data-ch04-waypoint]")
      ?.getAttribute("data-x");
    expect(before).toBeTruthy();
    xMul = 7;
    act(() => {
      bridge.fire();
    });
    const after = document
      .querySelector("[data-ch04-waypoint]")
      ?.getAttribute("data-x");
    expect(after).not.toBe(before);
  });
});

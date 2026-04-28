/**
 * Tests for the Carlos path progress controller (W3 Ch7 — T3.10).
 *
 * The W2 `carlosPath` layer pre-registered a LineString trace with
 * visibility:none. W3 Ch7 reveals it AND draws it progressively. The
 * controller exposes a small typed API:
 *
 *   - `setCarlosPathProgress(map, progress)` — paints the line with a
 *     progress-tied gradient (0 = invisible, 1 = fully drawn). Idempotent.
 *   - `setCarlosPathVisible(map, visible)` — flips layer visibility.
 *   - `revertCarlosPath(map)` — restores W2 hidden state for cleanup.
 */
import { describe, it, expect, vi } from "vitest";
import {
  setCarlosPathProgress,
  setCarlosPathVisible,
  revertCarlosPath,
  CARLOS_PATH_LINE_ID,
} from "../carlosPathProgress";

import type { MapboxLikeMap } from "../types";

// Build a Mapbox-like mock satisfying both the runtime contract and the
// nominal MapboxLikeMap surface. We cast to MapboxLikeMap at the call
// site to skirt vi.fn's overly-narrow generic signature.
interface FakeMap {
  setPaintProperty: ReturnType<typeof vi.fn>;
  setLayoutProperty: ReturnType<typeof vi.fn>;
  getLayer: ReturnType<typeof vi.fn>;
}

function fakeMap(): { map: FakeMap & MapboxLikeMap; calls: Array<{ method: string; args: unknown[] }> } {
  const calls: Array<{ method: string; args: unknown[] }> = [];
  const map = {
    addSource: vi.fn(),
    removeSource: vi.fn(),
    addLayer: vi.fn(),
    removeLayer: vi.fn(),
    getSource: vi.fn(() => undefined),
    getLayer: vi.fn(() => ({})),
    setPaintProperty: vi.fn((...args: unknown[]) => {
      calls.push({ method: "setPaintProperty", args });
    }),
    setLayoutProperty: vi.fn((...args: unknown[]) => {
      calls.push({ method: "setLayoutProperty", args });
    }),
  } as unknown as FakeMap & MapboxLikeMap;
  return { map, calls };
}

describe("setCarlosPathProgress — progress-tied gradient", () => {
  it("clamps progress to [0,1] and writes line-gradient", () => {
    const { map } = fakeMap();
    setCarlosPathProgress(map, -0.5);
    expect(map.setPaintProperty).toHaveBeenCalled();
    const args = map.setPaintProperty.mock.calls[0];
    expect(args[0]).toBe(CARLOS_PATH_LINE_ID);
    expect(args[1]).toBe("line-gradient");
  });

  it("writes opacity 0 at progress 0 (line is invisible until Ch7 starts)", () => {
    const { map } = fakeMap();
    setCarlosPathProgress(map, 0);
    const opacityCall = map.setPaintProperty.mock.calls.find(
      (c) => c[1] === "line-opacity",
    );
    expect(opacityCall).toBeDefined();
    expect(opacityCall![2]).toBe(0);
  });

  it("writes opacity > 0 at progress > 0", () => {
    const { map } = fakeMap();
    setCarlosPathProgress(map, 0.5);
    const opacityCall = map.setPaintProperty.mock.calls.find(
      (c) => c[1] === "line-opacity",
    );
    expect(opacityCall).toBeDefined();
    expect(typeof opacityCall![2]).toBe("number");
    expect(opacityCall![2] as number).toBeGreaterThan(0);
  });

  it("is a no-op when the layer is not yet registered", () => {
    const { map } = fakeMap();
    map.getLayer.mockReturnValueOnce(undefined);
    setCarlosPathProgress(map, 0.5);
    expect(map.setPaintProperty).not.toHaveBeenCalled();
  });
});

describe("setCarlosPathVisible — visibility flip", () => {
  it("sets visibility to 'visible' when true", () => {
    const { map } = fakeMap();
    setCarlosPathVisible(map, true);
    expect(map.setLayoutProperty).toHaveBeenCalledWith(
      CARLOS_PATH_LINE_ID,
      "visibility",
      "visible",
    );
  });

  it("sets visibility to 'none' when false", () => {
    const { map } = fakeMap();
    setCarlosPathVisible(map, false);
    expect(map.setLayoutProperty).toHaveBeenCalledWith(
      CARLOS_PATH_LINE_ID,
      "visibility",
      "none",
    );
  });
});

describe("revertCarlosPath — restore W2 hidden state", () => {
  it("hides the layer", () => {
    const { map } = fakeMap();
    revertCarlosPath(map);
    expect(map.setLayoutProperty).toHaveBeenCalledWith(
      CARLOS_PATH_LINE_ID,
      "visibility",
      "none",
    );
  });
});

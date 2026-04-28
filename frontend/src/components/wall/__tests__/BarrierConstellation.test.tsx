/**
 * W3 Driver B — BarrierConstellation tests (T3.14).
 *
 * The 3D constellation is a react-three-fiber `<Canvas>`. jsdom has no
 * WebGL, so we mock `@react-three/fiber` to a thin shell that just renders
 * its children. This still validates:
 *
 *   - Node count matches the 33-node graph
 *   - Edges resolve to existing node ids (cross-checked via DOM-attribute
 *     emission so the renderer's prop wiring is exercised)
 *   - Breathing animation is rate-limited (we assert the animation hook
 *     publishes a typed phase with a sane frequency)
 *   - Reduced-motion is honored (no breathing when set)
 *   - pathCompleteness=1 lights all edges; pathCompleteness=0 lights none
 */
import React from "react";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";

// Mock react-three-fiber: render a plain DOM tree so we can inspect props.
vi.mock("@react-three/fiber", () => ({
  Canvas: ({ children, ...rest }: React.PropsWithChildren<Record<string, unknown>>) =>
    React.createElement(
      "div",
      { "data-testid": "r3f-canvas", "data-r3f-mock": "true", ...rest },
      children,
    ),
  useFrame: () => undefined,
}));

import { BarrierConstellation } from "../BarrierConstellation";
import { BARRIER_GRAPH } from "@/lib/wall/data/barrierGraph";

beforeEach(() => {
  cleanup();
});

describe("BarrierConstellation — render shape", () => {
  it("renders a Canvas wrapper", () => {
    render(<BarrierConstellation pathCompleteness={1} />);
    expect(screen.getByTestId("r3f-canvas")).toBeInTheDocument();
  });

  it("emits one node element per BARRIER_GRAPH.nodes entry", () => {
    render(<BarrierConstellation pathCompleteness={1} />);
    const nodes = screen.getAllByTestId(/^constellation-node-/);
    expect(nodes).toHaveLength(BARRIER_GRAPH.nodes.length);
  });

  it("emits one edge element per BARRIER_GRAPH.edges entry", () => {
    render(<BarrierConstellation pathCompleteness={1} />);
    const edges = screen.getAllByTestId(/^constellation-edge-/);
    expect(edges).toHaveLength(BARRIER_GRAPH.edges.length);
  });

  it("each edge declares data-from and data-to referencing real node ids", () => {
    render(<BarrierConstellation pathCompleteness={1} />);
    const edges = screen.getAllByTestId(/^constellation-edge-/);
    const ids = new Set(BARRIER_GRAPH.nodes.map((n) => n.id));
    for (const e of edges) {
      const from = e.getAttribute("data-from");
      const to = e.getAttribute("data-to");
      expect(from).not.toBeNull();
      expect(to).not.toBeNull();
      expect(ids.has(from!)).toBe(true);
      expect(ids.has(to!)).toBe(true);
    }
  });
});

describe("BarrierConstellation — pathCompleteness lights edges", () => {
  it("data-illuminated='false' on every edge when pathCompleteness=0", () => {
    render(<BarrierConstellation pathCompleteness={0} />);
    const edges = screen.getAllByTestId(/^constellation-edge-/);
    for (const e of edges) {
      expect(e.getAttribute("data-illuminated")).toBe("false");
    }
  });

  it("data-illuminated='true' on every edge when pathCompleteness=1", () => {
    render(<BarrierConstellation pathCompleteness={1} />);
    const edges = screen.getAllByTestId(/^constellation-edge-/);
    for (const e of edges) {
      expect(e.getAttribute("data-illuminated")).toBe("true");
    }
  });
});

describe("BarrierConstellation — breathing animation rate", () => {
  it("publishes data-breathing-hz <= 0.2 (low-frequency drift)", () => {
    render(<BarrierConstellation pathCompleteness={0.5} />);
    const root = screen.getByTestId("constellation-root");
    const hz = Number(root.getAttribute("data-breathing-hz"));
    expect(hz).toBeGreaterThan(0);
    expect(hz).toBeLessThanOrEqual(0.2);
  });

  it("data-reduced-motion='true' disables breathing", () => {
    render(<BarrierConstellation pathCompleteness={0.5} reducedMotion />);
    const root = screen.getByTestId("constellation-root");
    expect(root.getAttribute("data-reduced-motion")).toBe("true");
    expect(Number(root.getAttribute("data-breathing-hz"))).toBe(0);
  });
});

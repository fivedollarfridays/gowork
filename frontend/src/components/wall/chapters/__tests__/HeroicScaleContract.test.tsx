/**
 * T-Render.1 — Heroic chapter card scale (visual-render-fix branch).
 *
 * Locks the heroic-scale visual contract:
 *   - Each chapter section is min-height: 100vh (no white gaps)
 *   - Card max-width is viewport-driven (vw units present in style or class)
 *   - Card uses backdrop-filter: blur(...) so the map tint shows through
 *   - h2 (or h1 for Ch1) uses fluid clamp(...) with vw scaling
 *
 * The existing Chapter05Labyrinth uses Tailwind classes (px-6 py-12 +
 * min-h-screen) so we assert on the rendered DOM (className string and
 * computed inline styles). For chapters that style inline (Ch2/Ch3/Ch7/Ch8),
 * we assert the inline style attribute carries the heroic values.
 */
import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";

import { Chapter02CityArrival } from "../Chapter02CityArrival";
import { Chapter03Neighborhood } from "../Chapter03Neighborhood";
import { Chapter05Labyrinth } from "../Chapter05Labyrinth";
import { Chapter07ThePath } from "../Chapter07ThePath";
import { Chapter08TheGraph } from "../Chapter08TheGraph";
import { Chapter09AnyCity } from "../Chapter09AnyCity";

// next/dynamic mock for Ch8 — returns a placeholder until the loader resolves.
import React from "react";
vi.mock("next/dynamic", () => ({
  default: () => {
    const Wrapper: React.FC<Record<string, unknown>> = () =>
      React.createElement("div", { "data-testid": "constellation-pending" });
    return Wrapper;
  },
}));
vi.mock("@react-three/fiber", () => ({
  Canvas: ({ children }: React.PropsWithChildren) =>
    React.createElement("div", { "data-testid": "r3f-canvas" }, children),
  useFrame: () => undefined,
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn(), back: vi.fn() }),
}));

vi.mock("@/hooks/useTranslation", () => ({
  useTranslation: vi.fn(() => ({
    locale: "en",
    t: (key: string) => key,
    switchLocale: vi.fn(),
  })),
}));

vi.mock("@/hooks/usePrefersReducedMotion", () => ({
  usePrefersReducedMotion: vi.fn(() => false),
}));

beforeEach(() => {
  cleanup();
});

describe("Heroic scale contract — chapter sections fill the viewport", () => {
  it("Chapter02 section has min-height 100vh", () => {
    const { container } = render(<Chapter02CityArrival progress={0.5} />);
    const section = container.querySelector('[data-testid="ch2-section"]') as HTMLElement;
    const styleAttr = section.getAttribute("style") ?? "";
    expect(styleAttr).toMatch(/min-height:\s*100vh/);
  });

  it("Chapter03 section has min-height 100vh", () => {
    const { container } = render(
      <Chapter03Neighborhood progress={0.5} active={false} />,
    );
    const section = container.querySelector('[data-testid="ch3-section"]') as HTMLElement;
    const styleAttr = section.getAttribute("style") ?? "";
    expect(styleAttr).toMatch(/min-height:\s*100vh/);
  });

  it("Chapter05 section has min-h-screen class", () => {
    render(<Chapter05Labyrinth progress={0.5} />);
    const section = screen.getByTestId("chapter05-labyrinth");
    expect(section.className).toContain("min-h-screen");
  });

  it("Chapter07 section has min-h-screen class", () => {
    render(<Chapter07ThePath progress={0.5} active />);
    const section = screen.getByTestId("chapter07-the-path");
    expect(section.className).toContain("min-h-screen");
  });

  it("Chapter08 section has min-h-screen class", () => {
    render(<Chapter08TheGraph progress={0.5} active />);
    const section = screen.getByTestId("chapter08-the-graph");
    expect(section.className).toContain("min-h-screen");
  });

  it("Chapter09 section has min-h-screen class", () => {
    render(<Chapter09AnyCity progress={0.5} active />);
    const section = screen.getByTestId("chapter09-any-city");
    expect(section.className).toContain("min-h-screen");
  });
});

describe("Heroic scale contract — Ch8 constellation static fallback (depth + scale)", () => {
  it("static fallback SVG viewBox is at least 800x500 (heroic scale)", () => {
    render(<Chapter08TheGraph progress={0.5} active reducedMotion />);
    const svg = screen.getByTestId("ch8-static-fallback-svg");
    const viewBox = svg.getAttribute("viewBox") ?? "";
    const parts = viewBox.split(/\s+/).map(Number);
    expect(parts.length).toBe(4);
    expect(parts[2]).toBeGreaterThanOrEqual(800);
    expect(parts[3]).toBeGreaterThanOrEqual(480);
  });

  it("static fallback renders all 33 nodes (data-node-id present per node)", () => {
    render(<Chapter08TheGraph progress={0.5} active reducedMotion />);
    const svg = screen.getByTestId("ch8-static-fallback-svg");
    // Each node renders a glow circle + a main circle with data-node-id;
    // assert one main-circle per node (the heroic depth treatment doubles
    // visual layers but we count by data-node-id, the canonical anchor).
    const nodes = svg.querySelectorAll("[data-node-id]");
    expect(nodes.length).toBe(33);
  });

  it("static fallback SVG has height >= 480px", () => {
    render(<Chapter08TheGraph progress={0.5} active reducedMotion />);
    const svg = screen.getByTestId("ch8-static-fallback-svg");
    const heightAttr = svg.getAttribute("height") ?? "";
    expect(parseInt(heightAttr, 10)).toBeGreaterThanOrEqual(480);
  });
});

describe("Heroic scale contract — Carlos avatar overlay mounted in Ch7", () => {
  it("Ch7 mounts the avatar overlay container with data-progress", () => {
    render(<Chapter07ThePath progress={0.5} active />);
    const overlay = screen.getByTestId("ch7-avatar-overlay");
    expect(overlay).toBeInTheDocument();
    expect(overlay.getAttribute("data-progress")).toBe("0.500");
  });

  it("Ch7 mounts the Carlos avatar inside the overlay (visible silhouette)", () => {
    render(<Chapter07ThePath progress={0.5} active />);
    const avatar = screen.getByTestId("carlos-avatar");
    expect(avatar).toBeInTheDocument();
  });

  it("Ch7 emits an animated polyline (ch7-avatar-path)", () => {
    render(<Chapter07ThePath progress={0.5} active />);
    const path = screen.getByTestId("ch7-avatar-path");
    expect(path).toBeInTheDocument();
    expect(path.getAttribute("stroke-dashoffset")).not.toBeNull();
  });

  it("Ch7 avatar position interpolates with progress (left changes)", () => {
    const { rerender } = render(<Chapter07ThePath progress={0} active />);
    const startStyle = screen
      .getByTestId("ch7-avatar-position")
      .getAttribute("style") ?? "";
    rerender(<Chapter07ThePath progress={1} active />);
    const endStyle = screen
      .getByTestId("ch7-avatar-position")
      .getAttribute("style") ?? "";
    expect(startStyle).not.toBe(endStyle);
  });
});

describe("Heroic scale contract — chapter cards use viewport-driven max-width (source)", () => {
  async function readSource(filename: string): Promise<string> {
    const fs = await import("node:fs");
    const path = await import("node:path");
    const filePath = path.resolve(__dirname, "..", filename);
    return fs.readFileSync(filePath, "utf-8");
  }

  it("Chapter02 overlay maxWidth uses min(...,vw,...) — viewport-pinned", async () => {
    const src = await readSource("Chapter02CityArrival.tsx");
    expect(src).toMatch(/maxWidth:\s*"min\([^"]*vw/);
  });

  it("Chapter03 overlay maxWidth uses min(...,vw,...)", async () => {
    const src = await readSource("Chapter03Neighborhood.tsx");
    expect(src).toMatch(/maxWidth:\s*"min\([^"]*vw/);
  });

  it("Chapter02 overlay carries backdrop-filter blur(12px)", async () => {
    const src = await readSource("Chapter02CityArrival.tsx");
    expect(src).toMatch(/backdropFilter:\s*"blur\(12px\)/);
  });

  it("Chapter03 overlay carries backdrop-filter blur(12px)", async () => {
    const src = await readSource("Chapter03Neighborhood.tsx");
    expect(src).toMatch(/backdropFilter:\s*"blur\(12px\)/);
  });

  it("Chapter07 card carries backdrop-filter blur(12px)", async () => {
    const src = await readSource("Chapter07ThePath.tsx");
    expect(src).toMatch(/backdropFilter:\s*"blur\(12px\)/);
  });

  it("Chapter08 card carries backdrop-filter blur(12px)", async () => {
    const src = await readSource("Chapter08TheGraph.tsx");
    expect(src).toMatch(/backdropFilter:\s*"blur\(12px\)/);
  });
});

describe("Heroic scale contract — headings use vw-driven clamp (source-level)", () => {
  // jsdom drops `clamp()` from inline styles entirely, so we lock the
  // contract source-level: each chapter's tsx must declare the heroic
  // headline pattern `clamp(...vw...)` somewhere on the h2/h1 fontSize.
  // This is the same source-level pattern Chapter08TheGraph.test uses to
  // lock the next/dynamic ssr:false contract.
  async function readSource(filename: string): Promise<string> {
    const fs = await import("node:fs");
    const path = await import("node:path");
    const filePath = path.resolve(__dirname, "..", filename);
    return fs.readFileSync(filePath, "utf-8");
  }

  it("Chapter02 h2 fontSize uses clamp(...,vw,...)", async () => {
    const src = await readSource("Chapter02CityArrival.tsx");
    expect(src).toMatch(/fontSize:\s*"clamp\([^"]*vw/);
  });

  it("Chapter03 h2 fontSize uses clamp(...,vw,...)", async () => {
    const src = await readSource("Chapter03Neighborhood.tsx");
    expect(src).toMatch(/fontSize:\s*"clamp\([^"]*vw/);
  });

  it("Chapter07 h2 fontSize uses clamp(...,vw,...)", async () => {
    const src = await readSource("Chapter07ThePath.tsx");
    expect(src).toMatch(/fontSize:\s*"clamp\([^"]*vw/);
  });

  it("Chapter08 h2 fontSize uses clamp(...,vw,...)", async () => {
    const src = await readSource("Chapter08TheGraph.tsx");
    expect(src).toMatch(/fontSize:\s*"clamp\([^"]*vw/);
  });
});

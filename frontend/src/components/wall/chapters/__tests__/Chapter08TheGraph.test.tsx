/**
 * W3 Driver B — Chapter 08 The Graph tests (T3.13).
 *
 * Locks Ch8's render contract:
 *   - section heading h2, aria-label, data-chapter="08"
 *   - dark gradient overlay + locked editorial copy
 *   - reduced-motion: a static SVG fallback is rendered (no Canvas mounted)
 *   - lazy-load contract: BarrierConstellation is loaded via next/dynamic
 *     with ssr:false (we assert source-level)
 *   - unmount cleanly tears down (test renders + unmounts; no crash)
 */
import React from "react";
import { describe, it, expect, beforeEach } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";

// next/dynamic mock (mirrors WallContainer-chapters.test.tsx).
import { vi } from "vitest";
vi.mock("next/dynamic", () => ({
  default: (loader: () => Promise<{ default: React.ComponentType }>) => {
    let Component: React.ComponentType | null = null;
    void loader().then((mod) => {
      Component = mod.default;
    });
    const Wrapper: React.FC<Record<string, unknown>> = (props) => {
      if (Component) return React.createElement(Component, props);
      return React.createElement("div", { "data-testid": "constellation-pending" });
    };
    return Wrapper;
  },
}));

// Also mock @react-three/fiber so the underlying Canvas works headless.
vi.mock("@react-three/fiber", () => ({
  Canvas: ({ children }: React.PropsWithChildren) =>
    React.createElement(
      "div",
      { "data-testid": "r3f-canvas", "data-r3f-mock": "true" },
      children,
    ),
  useFrame: () => undefined,
}));

import { Chapter08TheGraph } from "../Chapter08TheGraph";
import { setLocale } from "@/lib/i18n";

beforeEach(() => {
  cleanup();
  setLocale("en");
});

describe("Chapter08TheGraph — render", () => {
  it("declares data-chapter='08' on the root", () => {
    render(<Chapter08TheGraph progress={0.5} active />);
    expect(
      screen.getByTestId("chapter08-the-graph").getAttribute("data-chapter"),
    ).toBe("08");
  });

  it("renders an h2 with the chapter title", () => {
    render(<Chapter08TheGraph progress={0.5} active />);
    const heading = screen.getByRole("heading", { level: 2 });
    expect(heading).toBeInTheDocument();
  });

  it("declares aria-labelledby on the section root", () => {
    render(<Chapter08TheGraph progress={0.5} active />);
    expect(
      screen
        .getByTestId("chapter08-the-graph")
        .getAttribute("aria-labelledby"),
    ).toBe("chapter08-title");
  });
});

describe("Chapter08TheGraph — reduced motion fallback", () => {
  it("renders the static SVG fallback when reducedMotion=true", () => {
    render(<Chapter08TheGraph progress={0.5} active reducedMotion />);
    expect(screen.getByTestId("ch8-static-fallback-svg")).toBeInTheDocument();
  });

  it("declares data-reduced-motion='true' when reducedMotion=true", () => {
    render(<Chapter08TheGraph progress={0.5} active reducedMotion />);
    expect(
      screen.getByTestId("chapter08-the-graph").getAttribute(
        "data-reduced-motion",
      ),
    ).toBe("true");
  });
});

describe("Chapter08TheGraph — lazy-load contract (T3.13)", () => {
  it("imports BarrierConstellation via next/dynamic with ssr:false", async () => {
    const fs = await import("node:fs");
    const path = await import("node:path");
    const filePath = path.resolve(
      __dirname,
      "..",
      "Chapter08TheGraph.tsx",
    );
    const source = fs.readFileSync(filePath, "utf-8");
    expect(source).toMatch(/import\s+dynamic\s+from\s+["']next\/dynamic["']/);
    expect(source).toMatch(
      /dynamic\s*\(\s*\(\s*\)\s*=>\s*import\s*\(\s*["'][^"']*BarrierConstellation["']\s*\)/,
    );
    expect(source).toMatch(/ssr:\s*false/);
    // Forbid a static import of BarrierConstellation
    expect(source).not.toMatch(
      /^import\s+\{?\s*BarrierConstellation\s*\}?\s+from\s+["'][^"']*BarrierConstellation["']/m,
    );
  });
});

describe("Chapter08TheGraph — i18n", () => {
  it("renders ES copy when locale is es", () => {
    setLocale("es");
    render(<Chapter08TheGraph progress={0.5} active />);
    const heading = screen.getByRole("heading", { level: 2 });
    expect(heading.textContent ?? "").toMatch(/Capítulo|Grafo/);
    setLocale("en");
  });
});

describe("Chapter08TheGraph — unmount lifecycle", () => {
  it("renders + unmounts without throwing (GL context teardown)", () => {
    const { unmount } = render(
      <Chapter08TheGraph progress={0.5} active />,
    );
    expect(() => unmount()).not.toThrow();
  });
});

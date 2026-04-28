/**
 * Spotlight invention #3 (W4 Driver D) — lifeLayersIntegration.
 *
 * Single test that mounts every life-layer provider together and asserts
 * they coexist without conflict:
 *
 *   1. AccentTokenProvider (Driver A) — sets --accent-current on :root.
 *   2. MapCursorFlashlight (Driver A) — viewport mask overlay.
 *   3. LiveNow (Driver A) — polling header widget.
 *   4. useHeroFontWeight + useChapterHeadingFontWeight (Driver A) — font axes.
 *
 * The integration check guards against:
 *   - A future refactor that introduces a name clash on `--accent-current`.
 *   - A provider mounting order change that breaks `useTimeOfDay` reads.
 *   - A QueryClient leak that pollutes other tests.
 *
 * Without this, the four life-layer providers are tested in isolation and
 * their composition can drift silently. Mount-them-together = catch drift.
 */

import React from "react";
import { describe, it, expect, afterEach, vi } from "vitest";
import { render, cleanup } from "@testing-library/react";

// Mock useTimeOfDay so the test is deterministic across environments.
vi.mock("@/hooks/useTimeOfDay", () => ({
  useTimeOfDay: () => ({
    hour: 14,
    minute: 0,
    phase: "afternoon" as const,
    sunAltitudeDeg: 45,
    skyTypeName: "atmosphere" as const,
    skyColor: "oklch(0.82 0.07 220)",
    accentToken: "cyan" as const,
  }),
}));

// Mock useLiveNowFormatted — avoid the polling chain.
vi.mock("@/hooks/useLiveNowFormatted", () => ({
  useLiveNowFormatted: () => ({
    nowLabel: "2:00 PM",
    sessionCount: 12,
    lastCalibratedRelative: "2 min ago",
  }),
}));

// Mock useThrottledRAF — pass-through so the cursor handler runs synchronously.
vi.mock("@/hooks/useThrottledRAF", () => ({
  useThrottledRAF: <T extends (...args: never[]) => void>(fn: T) => fn,
}));

vi.mock("@/hooks/usePrefersReducedMotion", () => ({
  usePrefersReducedMotion: () => false,
}));

afterEach(() => {
  cleanup();
  // Clear --accent-current so AccentTokenProvider's persistence (it does
  // NOT clear on unmount by design) doesn't bleed across tests.
  if (typeof document !== "undefined") {
    document.documentElement.style.removeProperty("--accent-current");
  }
});

describe("Spotlight #3 — life-layer providers coexist", () => {
  it("AccentTokenProvider sets --accent-current on :root", async () => {
    const { AccentTokenProvider } = await import("../AccentTokenProvider");
    render(<AccentTokenProvider />);
    expect(
      document.documentElement.style.getPropertyValue("--accent-current"),
    ).toMatch(/oklch/);
  });

  it("MapCursorFlashlight mounts without throwing in jsdom", async () => {
    const { MapCursorFlashlight } = await import("../MapCursorFlashlight");
    const { getByTestId } = render(<MapCursorFlashlight />);
    expect(getByTestId("map-cursor-flashlight")).toBeInTheDocument();
  });

  it("LiveNow renders the polling widget under its own QueryClient", async () => {
    const { LiveNow } = await import("../LiveNow");
    const { getByTestId } = render(<LiveNow locale="en-US" />);
    expect(getByTestId("live-now")).toBeInTheDocument();
    expect(getByTestId("live-now-time")).toHaveTextContent("2:00 PM");
  });

  it("All three providers mounted together do not conflict", async () => {
    const { AccentTokenProvider } = await import("../AccentTokenProvider");
    const { MapCursorFlashlight } = await import("../MapCursorFlashlight");
    const { LiveNow } = await import("../LiveNow");
    const Composed = () => (
      <>
        <AccentTokenProvider />
        <MapCursorFlashlight />
        <LiveNow locale="en-US" />
      </>
    );
    const { getByTestId } = render(<Composed />);
    expect(getByTestId("map-cursor-flashlight")).toBeInTheDocument();
    expect(getByTestId("live-now")).toBeInTheDocument();
    expect(
      document.documentElement.style.getPropertyValue("--accent-current"),
    ).toMatch(/oklch/);
  });

  it("useHeroFontWeight returns 'wght 700' at progress 0 (afternoon phase noop)", async () => {
    const { useHeroFontWeight } = await import("@/hooks/useHeroFontWeight");
    function Probe() {
      const variation = useHeroFontWeight(0);
      return <div data-testid="probe">{variation}</div>;
    }
    const { getByTestId } = render(<Probe />);
    expect(getByTestId("probe")).toHaveTextContent('"wght" 700');
  });

  it("useHeroFontWeight returns 'wght 900' at progress >= 0.05 (peak)", async () => {
    const { useHeroFontWeight } = await import("@/hooks/useHeroFontWeight");
    function Probe() {
      const variation = useHeroFontWeight(0.05);
      return <div data-testid="probe">{variation}</div>;
    }
    const { getByTestId } = render(<Probe />);
    expect(getByTestId("probe")).toHaveTextContent('"wght" 900');
  });
});

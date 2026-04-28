/**
 * W4 Driver B — Spotlight invention #3 (useResponsiveTier).
 *
 * # Why this exists
 *
 * `useDeviceCapability` (W1) classifies HARDWARE tier (low/medium/high) but
 * does NOT classify VIEWPORT tier. The dispatch's mobile-fallback story
 * needs both:
 *
 *   - Mobile (innerWidth < 768)            → static fallback, editorial only
 *   - Tablet (768 ≤ innerWidth < 1024)     → Mapbox at lower zoom
 *   - Desktop (innerWidth ≥ 1024)          → full cinematic experience
 *
 * This hook centralises the viewport classification so chapter components,
 * WallContainer, and judges-on-phones telemetry don't each re-derive it
 * from `window.innerWidth`. SSR-safe (returns 'desktop' default before
 * the first effect fires).
 *
 * Resize-aware: subscribes to `window.resize` so a phone rotated to
 * landscape (innerWidth crossing 768) re-tiers correctly.
 */
import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useResponsiveTier } from "../useResponsiveTier";

const ORIGINAL_WIDTH = window.innerWidth;

function setInnerWidth(value: number): void {
  Object.defineProperty(window, "innerWidth", {
    value,
    configurable: true,
    writable: true,
  });
  window.dispatchEvent(new Event("resize"));
}

describe("useResponsiveTier", () => {
  afterEach(() => {
    setInnerWidth(ORIGINAL_WIDTH);
  });

  it("classifies innerWidth=320 as mobile", () => {
    setInnerWidth(320);
    const { result } = renderHook(() => useResponsiveTier());
    expect(result.current.tier).toBe("mobile");
    expect(result.current.isMobile).toBe(true);
    expect(result.current.isTablet).toBe(false);
    expect(result.current.isDesktop).toBe(false);
  });

  it("classifies innerWidth=767 as mobile (boundary)", () => {
    setInnerWidth(767);
    const { result } = renderHook(() => useResponsiveTier());
    expect(result.current.tier).toBe("mobile");
  });

  it("classifies innerWidth=768 as tablet (lower boundary)", () => {
    setInnerWidth(768);
    const { result } = renderHook(() => useResponsiveTier());
    expect(result.current.tier).toBe("tablet");
    expect(result.current.isTablet).toBe(true);
  });

  it("classifies innerWidth=900 as tablet", () => {
    setInnerWidth(900);
    const { result } = renderHook(() => useResponsiveTier());
    expect(result.current.tier).toBe("tablet");
  });

  it("classifies innerWidth=1023 as tablet (upper boundary)", () => {
    setInnerWidth(1023);
    const { result } = renderHook(() => useResponsiveTier());
    expect(result.current.tier).toBe("tablet");
  });

  it("classifies innerWidth=1024 as desktop", () => {
    setInnerWidth(1024);
    const { result } = renderHook(() => useResponsiveTier());
    expect(result.current.tier).toBe("desktop");
    expect(result.current.isDesktop).toBe(true);
  });

  it("classifies innerWidth=1920 as desktop", () => {
    setInnerWidth(1920);
    const { result } = renderHook(() => useResponsiveTier());
    expect(result.current.tier).toBe("desktop");
  });

  it("re-classifies on window resize (phone → tablet via rotation)", () => {
    setInnerWidth(400);
    const { result } = renderHook(() => useResponsiveTier());
    expect(result.current.tier).toBe("mobile");
    act(() => {
      setInnerWidth(900);
    });
    expect(result.current.tier).toBe("tablet");
  });

  it("re-classifies on window resize (desktop → mobile via shrink)", () => {
    setInnerWidth(1440);
    const { result } = renderHook(() => useResponsiveTier());
    expect(result.current.tier).toBe("desktop");
    act(() => {
      setInnerWidth(360);
    });
    expect(result.current.tier).toBe("mobile");
  });

  it("exposes width so consumers can do bespoke breakpoint logic", () => {
    setInnerWidth(900);
    const { result } = renderHook(() => useResponsiveTier());
    expect(result.current.width).toBe(900);
  });
});

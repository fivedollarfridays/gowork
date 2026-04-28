/**
 * W3 Driver B — CarlosAvatar tests (T3.11).
 *
 * Locks the avatar contract:
 *   - SVG silhouette renders (data-testid="carlos-avatar")
 *   - lng/lat updates are derived from `avatarPath.positionAt(t)`
 *   - footstep audio is rate-limited (NOT a barrage)
 *   - reduced-motion: walking-stride animation disabled
 *   - data-segment-index reflects the active leg (per-leg highlight feed)
 */
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import { CarlosAvatar } from "../CarlosAvatar";
import * as soundLib from "@/lib/wall/sound";

beforeEach(() => {
  cleanup();
  vi.restoreAllMocks();
  // Force unmuted so play() actually fires
  soundLib.setMuted(false);
});

afterEach(() => {
  soundLib.setMuted(true);
  cleanup();
});

describe("CarlosAvatar — render", () => {
  it("renders the silhouette SVG with role='img'", () => {
    render(<CarlosAvatar progress={0.0} />);
    const avatar = screen.getByTestId("carlos-avatar");
    expect(avatar).toBeInTheDocument();
    expect(avatar.getAttribute("role")).toBe("img");
  });

  it("declares an accessible label sourced from i18n", () => {
    render(<CarlosAvatar progress={0.5} />);
    const avatar = screen.getByTestId("carlos-avatar");
    expect(avatar.getAttribute("aria-label")).toMatch(/.+/);
  });

  it("declares data-progress as the clamped t", () => {
    render(<CarlosAvatar progress={1.5} />);
    const avatar = screen.getByTestId("carlos-avatar");
    expect(avatar.getAttribute("data-progress")).toBe("1.000");
  });
});

describe("CarlosAvatar — lng/lat interpolation along the path", () => {
  it("emits data-lng/data-lat at progress=0 (home anchor)", () => {
    render(<CarlosAvatar progress={0} />);
    const avatar = screen.getByTestId("carlos-avatar");
    const lng = Number(avatar.getAttribute("data-lng"));
    const lat = Number(avatar.getAttribute("data-lat"));
    // Home pin is at -97.293 / 32.713
    expect(lng).toBeCloseTo(-97.293, 3);
    expect(lat).toBeCloseTo(32.713, 3);
  });

  it("emits different lng/lat at progress=0 vs progress=1", () => {
    const { rerender } = render(<CarlosAvatar progress={0} />);
    const lng0 = Number(
      screen.getByTestId("carlos-avatar").getAttribute("data-lng"),
    );
    rerender(<CarlosAvatar progress={1} />);
    const lng1 = Number(
      screen.getByTestId("carlos-avatar").getAttribute("data-lng"),
    );
    expect(lng0).not.toBeCloseTo(lng1, 3);
  });

  it("emits data-segment-index reflecting the active leg", () => {
    render(<CarlosAvatar progress={0.05} />);
    const segIdx = Number(
      screen.getByTestId("carlos-avatar").getAttribute("data-segment-index"),
    );
    expect(Number.isFinite(segIdx)).toBe(true);
    expect(segIdx).toBeGreaterThanOrEqual(0);
  });
});

describe("CarlosAvatar — footstep rate-limit", () => {
  it("does NOT fire footstep on every progress update (rate-limited)", () => {
    const playSpy = vi.spyOn(soundLib, "play").mockImplementation(() => undefined);
    const { rerender } = render(<CarlosAvatar progress={0} />);
    // Drive a tiny delta that should NOT cross the rate-limit threshold
    rerender(<CarlosAvatar progress={0.005} />);
    rerender(<CarlosAvatar progress={0.01} />);
    rerender(<CarlosAvatar progress={0.015} />);
    // First mount may fire one footstep; subsequent micro-updates must NOT
    expect(playSpy.mock.calls.length).toBeLessThanOrEqual(1);
  });

  it("fires footstep on a large progress jump (crossed threshold)", () => {
    const playSpy = vi.spyOn(soundLib, "play").mockImplementation(() => undefined);
    const { rerender } = render(<CarlosAvatar progress={0} />);
    rerender(<CarlosAvatar progress={0.5} />);
    expect(playSpy.mock.calls.length).toBeGreaterThanOrEqual(1);
    expect(playSpy).toHaveBeenCalledWith("footstep");
  });
});

describe("CarlosAvatar — reduced motion", () => {
  it("declares data-reduced-motion='true' when prop is set", () => {
    render(<CarlosAvatar progress={0.5} reducedMotion />);
    expect(
      screen.getByTestId("carlos-avatar").getAttribute("data-reduced-motion"),
    ).toBe("true");
  });

  it("does NOT fire footstep audio when reducedMotion=true", () => {
    const playSpy = vi.spyOn(soundLib, "play").mockImplementation(() => undefined);
    const { rerender } = render(<CarlosAvatar progress={0} reducedMotion />);
    rerender(<CarlosAvatar progress={0.5} reducedMotion />);
    expect(playSpy).not.toHaveBeenCalled();
  });
});

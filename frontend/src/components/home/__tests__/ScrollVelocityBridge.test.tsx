/**
 * polish-2 T56 — ScrollVelocityBridge tests.
 *
 * Verifies the bridge writes `body[data-scroll-velocity="fast"]` when the
 * `useScrollVelocity` hook reports fast scrolling, and clears the attr
 * when scroll slows again.
 *
 * polish-2 T57 — battery-aware degradation. The same bridge writes
 * `body[data-battery-low]` when `useBatteryAware().isLow` is true.
 */
import React from "react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { render, cleanup } from "@testing-library/react";

vi.mock("@/hooks/useScrollVelocity", () => ({
  useScrollVelocity: vi.fn(),
}));
vi.mock("@/hooks/useBatteryAware", () => ({
  useBatteryAware: vi.fn(),
}));
vi.mock("@/hooks/useIdleState", () => ({
  useIdleState: vi.fn(),
}));

import { useScrollVelocity } from "@/hooks/useScrollVelocity";
import { useBatteryAware } from "@/hooks/useBatteryAware";
import { useIdleState } from "@/hooks/useIdleState";
import { ScrollVelocityBridge } from "../ScrollVelocityBridge";

const velocityMock = vi.mocked(useScrollVelocity);
const batteryMock = vi.mocked(useBatteryAware);
const idleMock = vi.mocked(useIdleState);

afterEach(() => {
  cleanup();
  document.body.removeAttribute("data-scroll-velocity");
  document.body.removeAttribute("data-battery-low");
  document.body.removeAttribute("data-idle");
  velocityMock.mockReset();
  batteryMock.mockReset();
  idleMock.mockReset();
});

function setMocks(opts: {
  fast?: boolean;
  battery?: { level: number | null; charging: boolean | null; isLow: boolean };
  idle?: boolean;
}): void {
  velocityMock.mockReturnValue({ velocity: opts.fast ? 5 : 0, isFast: !!opts.fast });
  batteryMock.mockReturnValue(
    opts.battery ?? { level: null, charging: null, isLow: false },
  );
  idleMock.mockReturnValue(!!opts.idle);
}

describe("ScrollVelocityBridge — T56 fast-scroll attr", () => {
  it("writes body[data-scroll-velocity='fast'] when isFast is true", () => {
    setMocks({ fast: true });
    render(<ScrollVelocityBridge />);
    expect(document.body.getAttribute("data-scroll-velocity")).toBe("fast");
  });

  it("does not write the attr when isFast is false", () => {
    setMocks({ fast: false });
    render(<ScrollVelocityBridge />);
    expect(document.body.hasAttribute("data-scroll-velocity")).toBe(false);
  });

  it("removes the attr on unmount", () => {
    setMocks({ fast: true });
    const { unmount } = render(<ScrollVelocityBridge />);
    expect(document.body.hasAttribute("data-scroll-velocity")).toBe(true);
    unmount();
    expect(document.body.hasAttribute("data-scroll-velocity")).toBe(false);
  });
});

describe("ScrollVelocityBridge — T57 battery-low attr", () => {
  it("writes body[data-battery-low] when battery.isLow is true", () => {
    setMocks({
      battery: { level: 0.15, charging: false, isLow: true },
    });
    render(<ScrollVelocityBridge />);
    expect(document.body.hasAttribute("data-battery-low")).toBe(true);
  });

  it("does not write the attr when battery.isLow is false", () => {
    setMocks({
      battery: { level: 0.5, charging: true, isLow: false },
    });
    render(<ScrollVelocityBridge />);
    expect(document.body.hasAttribute("data-battery-low")).toBe(false);
  });
});

describe("ScrollVelocityBridge — T59 idle-state attr (Ch4 ambient)", () => {
  it("writes body[data-idle='true'] when idle is true", () => {
    setMocks({ idle: true });
    render(<ScrollVelocityBridge />);
    expect(document.body.getAttribute("data-idle")).toBe("true");
  });

  it("does not write the attr when idle is false", () => {
    setMocks({ idle: false });
    render(<ScrollVelocityBridge />);
    expect(document.body.hasAttribute("data-idle")).toBe(false);
  });
});

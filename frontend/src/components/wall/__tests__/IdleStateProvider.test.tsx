/**
 * T4.D.7 — IdleStateProvider (Wave 4 polish).
 *
 * After 30s of no input, the provider sets `data-life-idle="true"` on
 * `:root`. Any component (BarrierConstellation orbital drift speedup,
 * PathLineHeader pulse) can opt in via CSS:
 *
 *   :root[data-life-idle="true"] .barrier-constellation { ... }
 *
 * Reverts on any input event. Reduced-motion: the attribute STILL sets
 * but consumer CSS should be no-op for reduced-motion (consumer
 * responsibility).
 *
 * This is the lightest-weight wiring: no React context plumbing, no
 * direct refs into Three.js, just a documented data attribute that any
 * existing component can pick up via stylesheet.
 */

import React from "react";
import { describe, it, expect, vi, afterEach, beforeEach } from "vitest";
import { render, cleanup, act } from "@testing-library/react";

const idleStateMock = vi.fn();
vi.mock("@/hooks/useIdleState", () => ({
  useIdleState: (ms?: number) => idleStateMock(ms),
}));

beforeEach(() => {
  idleStateMock.mockReset();
});

afterEach(() => {
  cleanup();
  if (typeof document !== "undefined") {
    document.documentElement.removeAttribute("data-life-idle");
  }
});

describe("T4.D.7 — IdleStateProvider sets data-life-idle on :root", () => {
  it("renders nothing visible", async () => {
    idleStateMock.mockReturnValue(false);
    const { IdleStateProvider } = await import("../IdleStateProvider");
    const { container } = render(<IdleStateProvider />);
    expect(container.firstChild).toBeNull();
  });

  it("does not set data-life-idle when not idle", async () => {
    idleStateMock.mockReturnValue(false);
    const { IdleStateProvider } = await import("../IdleStateProvider");
    render(<IdleStateProvider />);
    expect(
      document.documentElement.getAttribute("data-life-idle"),
    ).not.toBe("true");
  });

  it("sets data-life-idle='true' on :root when idle", async () => {
    idleStateMock.mockReturnValue(true);
    const { IdleStateProvider } = await import("../IdleStateProvider");
    render(<IdleStateProvider />);
    expect(document.documentElement.getAttribute("data-life-idle")).toBe(
      "true",
    );
  });

  it("clears data-life-idle when transitioning back to active", async () => {
    idleStateMock.mockReturnValue(true);
    const { IdleStateProvider } = await import("../IdleStateProvider");
    const { rerender } = render(<IdleStateProvider />);
    expect(document.documentElement.getAttribute("data-life-idle")).toBe(
      "true",
    );
    idleStateMock.mockReturnValue(false);
    act(() => {
      rerender(<IdleStateProvider />);
    });
    expect(
      document.documentElement.getAttribute("data-life-idle"),
    ).not.toBe("true");
  });

  it("removes data-life-idle on unmount (no leak)", async () => {
    idleStateMock.mockReturnValue(true);
    const { IdleStateProvider } = await import("../IdleStateProvider");
    const { unmount } = render(<IdleStateProvider />);
    expect(document.documentElement.getAttribute("data-life-idle")).toBe(
      "true",
    );
    unmount();
    expect(
      document.documentElement.getAttribute("data-life-idle"),
    ).not.toBe("true");
  });

  it("forwards a custom idleMs prop to useIdleState", async () => {
    idleStateMock.mockReturnValue(false);
    const { IdleStateProvider } = await import("../IdleStateProvider");
    render(<IdleStateProvider idleMs={5_000} />);
    expect(idleStateMock).toHaveBeenCalledWith(5_000);
  });
});

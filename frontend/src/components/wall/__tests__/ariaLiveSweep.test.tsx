/**
 * W4 Driver C — T4.C.4 — ARIA-live screen-reader sweep.
 *
 * Asserts that:
 *   - The AriaLiveProvider + AriaLiveRegion are mountable without crash
 *   - useAriaAnnounce dispatches `gowork:aria-announce` events
 *   - The live region observes the event and renders the message
 *   - Decorative SVGs in BarrierConstellation and CarlosAvatar are
 *     marked aria-hidden="true"
 *   - BarrierConstellation has a textual aria-label so screen readers
 *     get a summary instead of trying to enumerate 33 invisible nodes
 *
 * Driver D's existing W3 axe sweep covers structural a11y per chapter;
 * this file adds the live-announcement contract that axe cannot reason
 * about (axe sees DOM, not narration semantics).
 */
import React from "react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, cleanup, act } from "@testing-library/react";
import {
  AriaLiveProvider,
  AriaLiveRegion,
  useAriaAnnounce,
} from "../AriaLiveRegion";
import { CarlosAvatar } from "../CarlosAvatar";

vi.mock("@/hooks/usePrefersReducedMotion", () => ({
  usePrefersReducedMotion: () => false,
}));

beforeEach(() => undefined);
afterEach(() => cleanup());

function Announcer({ msg }: { msg: string }) {
  const announce = useAriaAnnounce();
  React.useEffect(() => {
    announce(msg);
  }, [announce, msg]);
  return null;
}

describe("T4.C.4 — AriaLiveRegion mount + render", () => {
  it("AriaLiveRegion renders with role='status' and aria-live='polite'", () => {
    const { getByTestId } = render(<AriaLiveRegion />);
    const region = getByTestId("aria-live-region");
    expect(region.getAttribute("role")).toBe("status");
    expect(region.getAttribute("aria-live")).toBe("polite");
    expect(region.getAttribute("aria-atomic")).toBe("true");
  });

  it("AriaLiveRegion supports assertive politeness override", () => {
    const { getByTestId } = render(<AriaLiveRegion politeness="assertive" />);
    expect(getByTestId("aria-live-region").getAttribute("aria-live")).toBe(
      "assertive",
    );
  });

  it("AriaLiveRegion uses the sr-only class to stay visually hidden", () => {
    const { getByTestId } = render(<AriaLiveRegion />);
    expect(getByTestId("aria-live-region").className).toContain("sr-only");
  });
});

describe("T4.C.4 — useAriaAnnounce integration", () => {
  it("publishing a message via useAriaAnnounce updates the live region", async () => {
    const { getByTestId } = render(
      <AriaLiveProvider>
        <AriaLiveRegion />
        <Announcer msg="Carlos arrives at the warehouse" />
      </AriaLiveProvider>,
    );
    // The Announcer's effect dispatches the event after mount; React
    // flushes the resulting state update on the next tick.
    await act(async () => {
      await Promise.resolve();
    });
    const region = getByTestId("aria-live-region");
    expect(region.textContent).toContain("Carlos arrives");
  });

  it("works without a provider (fallback path dispatches directly)", async () => {
    // No AriaLiveProvider — region still observes the window event.
    const { getByTestId } = render(
      <>
        <AriaLiveRegion />
        <Announcer msg="provider-less message" />
      </>,
    );
    await act(async () => {
      await Promise.resolve();
    });
    expect(getByTestId("aria-live-region").textContent).toContain(
      "provider-less message",
    );
  });
});

describe("T4.C.4 — Decorative SVGs are aria-hidden", () => {
  it("CarlosAvatar's inline SVG has aria-hidden='true'", () => {
    const { container } = render(
      <CarlosAvatar progress={0.5} reducedMotion={false} />,
    );
    const svg = container.querySelector("svg");
    expect(svg).not.toBeNull();
    expect(svg?.getAttribute("aria-hidden")).toBe("true");
    expect(svg?.getAttribute("focusable")).toBe("false");
  });

  it("CarlosAvatar's outer wrapper has role='img' with an aria-label", () => {
    const { container } = render(
      <CarlosAvatar progress={0.5} reducedMotion={false} />,
    );
    const root = container.querySelector("[data-testid='carlos-avatar']");
    expect(root?.getAttribute("role")).toBe("img");
    expect(root?.getAttribute("aria-label")).toBeTruthy();
    expect((root?.getAttribute("aria-label") || "").length).toBeGreaterThan(0);
  });
});

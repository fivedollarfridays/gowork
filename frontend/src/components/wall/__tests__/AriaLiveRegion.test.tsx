/**
 * W1 Driver C — T1.64 AriaLiveRegion.
 *
 * Module-level scaffolding for screen-reader chapter announcements
 * consumed in W2. This test guards :
 *   - The provider mounts an aria-live region with the requested politeness.
 *   - The hook `useAriaAnnounce` writes through to the region.
 *   - Default politeness is "polite" (per W3C ARIA-LIVE recommendations
 *     for non-urgent navigation announcements).
 */
import { describe, it, expect } from "vitest";
import { act, render, renderHook, screen } from "@testing-library/react";
import {
  AriaLiveRegion,
  AriaLiveProvider,
  useAriaAnnounce,
} from "../AriaLiveRegion";

describe("AriaLiveRegion", () => {
  it("renders a live region with default politeness=polite", () => {
    render(<AriaLiveRegion />);
    const live = screen.getByTestId("aria-live-region");
    expect(live).toHaveAttribute("aria-live", "polite");
    expect(live).toHaveAttribute("aria-atomic", "true");
  });

  it("supports assertive politeness", () => {
    render(<AriaLiveRegion politeness="assertive" />);
    const live = screen.getByTestId("aria-live-region");
    expect(live).toHaveAttribute("aria-live", "assertive");
  });

  it("the useAriaAnnounce hook updates the live region content", () => {
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <AriaLiveProvider>
        <AriaLiveRegion />
        {children}
      </AriaLiveProvider>
    );
    const { result } = renderHook(() => useAriaAnnounce(), { wrapper });
    act(() => {
      result.current("Chapter 1 of 10 — Continental");
    });
    const live = screen.getByTestId("aria-live-region");
    expect(live).toHaveTextContent(/Chapter 1 of 10/);
  });
});

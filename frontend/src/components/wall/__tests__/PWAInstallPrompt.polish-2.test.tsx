/**
 * polish-2 Driver D — T41 PWAInstallPrompt polish.
 *
 * Extends the W7 base contract:
 *   - 12s auto-hide if the user takes no action.
 *   - localStorage `gowork-pwa-dismissed=1` persists 30 days; while the
 *     timestamp is fresh, `beforeinstallprompt` does NOT re-surface.
 *   - Chip styling: bottom-LEFT (not -right), brand mark + "Install
 *     GoWork" + dismiss X. We assert by data-testid + aria-label.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { act, render, screen } from "@testing-library/react";
import { PWAInstallPrompt } from "../PWAInstallPrompt";

interface FakePromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
  preventDefault: () => void;
}

function fireBeforeInstall() {
  const evt: Partial<FakePromptEvent> = {
    type: "beforeinstallprompt",
    prompt: () => Promise.resolve(),
    userChoice: Promise.resolve({ outcome: "accepted" }),
    preventDefault: () => {},
  };
  window.dispatchEvent(new CustomEvent("beforeinstallprompt", { detail: evt }));
}

beforeEach(() => {
  localStorage.clear();
  vi.useFakeTimers();
});

afterEach(() => {
  vi.useRealTimers();
  localStorage.clear();
});

describe("PWAInstallPrompt — polish-2 T41 polish", () => {
  it("auto-hides after 12s with no interaction", () => {
    render(<PWAInstallPrompt />);
    act(() => {
      fireBeforeInstall();
    });
    expect(screen.queryByRole("button", { name: /^install$/i })).not.toBeNull();

    act(() => {
      vi.advanceTimersByTime(12_000);
    });
    expect(screen.queryByRole("button", { name: /^install$/i })).toBeNull();
  });

  it("persists dismissal in localStorage with key `gowork-pwa-dismissed`", () => {
    render(<PWAInstallPrompt />);
    act(() => {
      fireBeforeInstall();
    });
    const dismiss = screen.getByRole("button", { name: /dismiss install/i });
    act(() => {
      dismiss.click();
    });
    const stored = localStorage.getItem("gowork-pwa-dismissed");
    expect(stored).toBeTruthy();
    // Stored as JSON containing a millis timestamp; parse + sanity-check.
    const parsed = JSON.parse(stored!);
    expect(typeof parsed.t).toBe("number");
    expect(parsed.t).toBeGreaterThan(0);
  });

  it("does NOT re-surface when dismissed within the 30-day window", () => {
    // Place a dismissal timestamp 5 minutes ago.
    localStorage.setItem(
      "gowork-pwa-dismissed",
      JSON.stringify({ t: Date.now() - 5 * 60_000 }),
    );
    render(<PWAInstallPrompt />);
    act(() => {
      fireBeforeInstall();
    });
    // The prompt event was suppressed because of the recent dismissal.
    expect(screen.queryByRole("button", { name: /^install$/i })).toBeNull();
  });

  it("RE-surfaces after the 30-day window has elapsed", () => {
    const THIRTY_ONE_DAYS_MS = 31 * 24 * 60 * 60_000;
    localStorage.setItem(
      "gowork-pwa-dismissed",
      JSON.stringify({ t: Date.now() - THIRTY_ONE_DAYS_MS }),
    );
    render(<PWAInstallPrompt />);
    act(() => {
      fireBeforeInstall();
    });
    expect(screen.queryByRole("button", { name: /^install$/i })).not.toBeNull();
  });

  it("renders the chip in the bottom-LEFT corner", () => {
    render(<PWAInstallPrompt />);
    act(() => {
      fireBeforeInstall();
    });
    const chip = screen.getByRole("region", { name: /install gowork/i });
    expect(chip.className).toMatch(/left-/);
    expect(chip.className).not.toMatch(/right-\d/);
  });

  it("renders an inline brand-mark SVG inside the chip", () => {
    const { container } = render(<PWAInstallPrompt />);
    act(() => {
      fireBeforeInstall();
    });
    const region = container.querySelector('[role="region"]');
    expect(region?.querySelector("[data-pwa-brand]")).not.toBeNull();
  });
});

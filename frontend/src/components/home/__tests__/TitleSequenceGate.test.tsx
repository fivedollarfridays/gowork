/**
 * polish-2 T49 — TitleSequenceGate tests.
 *
 * Mounts the wall TitleSequence on first visit. Subsequent visits
 * (sessionStorage flag) and reduced-motion users skip the sequence.
 */
import React from "react";
import { describe, it, expect, vi, afterEach, beforeEach } from "vitest";
import { render, cleanup, act } from "@testing-library/react";
import { TranslationProvider } from "@/hooks/useTranslation";

vi.mock("@/hooks/usePrefersReducedMotion", () => ({
  usePrefersReducedMotion: vi.fn(() => false),
}));

import { usePrefersReducedMotion } from "@/hooks/usePrefersReducedMotion";
import { TitleSequenceGate } from "../TitleSequenceGate";

const reducedMock = vi.mocked(usePrefersReducedMotion);

const SESSION_KEY = "gowork-title-seen";

beforeEach(() => {
  reducedMock.mockReturnValue(false);
  sessionStorage.clear();
});

afterEach(() => {
  cleanup();
  sessionStorage.clear();
});

function wrap(node: React.ReactNode) {
  return render(<TranslationProvider>{node}</TranslationProvider>);
}

describe("TitleSequenceGate (polish-2 T49)", () => {
  it("renders the title sequence on first visit", () => {
    const { container } = wrap(<TitleSequenceGate />);
    expect(container.querySelector("[data-title-sequence]")).not.toBeNull();
  });

  it("does not render when sessionStorage flag is set", () => {
    sessionStorage.setItem(SESSION_KEY, "1");
    const { container } = wrap(<TitleSequenceGate />);
    expect(container.querySelector("[data-title-sequence]")).toBeNull();
  });

  it("does not render under prefers-reduced-motion", () => {
    reducedMock.mockReturnValue(true);
    const { container } = wrap(<TitleSequenceGate />);
    expect(container.querySelector("[data-title-sequence]")).toBeNull();
  });

  it("sets the sessionStorage flag once the sequence completes", () => {
    vi.useFakeTimers();
    try {
      wrap(<TitleSequenceGate durationMs={400} />);
      act(() => {
        vi.advanceTimersByTime(450);
      });
      expect(sessionStorage.getItem(SESSION_KEY)).toBe("1");
    } finally {
      vi.useRealTimers();
    }
  });

  it("after the sequence completes the gate hides the sequence", () => {
    vi.useFakeTimers();
    try {
      const { container } = wrap(<TitleSequenceGate durationMs={400} />);
      act(() => {
        vi.advanceTimersByTime(800);
      });
      expect(container.querySelector("[data-title-sequence]")).toBeNull();
    } finally {
      vi.useRealTimers();
    }
  });
});

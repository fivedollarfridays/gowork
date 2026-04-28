/**
 * W2 Driver C — Ch4 sub-chapter transition integration tests.
 *
 * Drive Chapter04TheWall through 4a → 4b → 4c → 4d and assert that
 *   - the active sub-chapter changes on each step
 *   - a fresh ARIA-live narration fires per step
 *   - a fresh sound trigger fires per step
 *   - data-subchapter on the rendered overlay matches
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, act } from "@testing-library/react";
import { Chapter04TheWall } from "../Chapter04TheWall";
import { setLocale } from "@/lib/i18n";
import * as soundLib from "@/lib/wall/sound";

const STEPS: { progress: number; expectedSub: string }[] = [
  { progress: 0.05, expectedSub: "4a" },
  { progress: 0.3, expectedSub: "4b" },
  { progress: 0.6, expectedSub: "4c" },
  { progress: 0.9, expectedSub: "4d" },
];

describe("Ch4 transitions — full 4a → 4d traversal", () => {
  let playSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    setLocale("en");
    playSpy = vi.spyOn(soundLib, "play").mockImplementation(() => undefined);
  });

  afterEach(() => {
    playSpy.mockRestore();
  });

  it("steps through all four sub-chapters and renders each in turn", () => {
    const { rerender } = render(<Chapter04TheWall progress={STEPS[0].progress} />);
    for (const step of STEPS) {
      act(() => {
        rerender(<Chapter04TheWall progress={step.progress} />);
      });
      expect(
        screen.getByTestId("ch4-subchapter").getAttribute("data-subchapter"),
      ).toBe(step.expectedSub);
    }
  });

  it("plays a sound on each unique sub-chapter entry (no replay within a sub)", () => {
    const heard: string[] = [];
    playSpy.mockImplementation((id: string) => {
      heard.push(id);
    });
    const { rerender } = render(<Chapter04TheWall progress={0.05} />);
    rerender(<Chapter04TheWall progress={0.1} />); // still 4a — no replay
    rerender(<Chapter04TheWall progress={0.3} />); // → 4b
    rerender(<Chapter04TheWall progress={0.35} />); // still 4b — no replay
    rerender(<Chapter04TheWall progress={0.6} />); // → 4c
    rerender(<Chapter04TheWall progress={0.9} />); // → 4d
    // Exactly 4 sound entries (one per unique sub-chapter).
    expect(heard).toHaveLength(4);
  });

  it("dispatches a fresh aria-announce on each sub-chapter entry", () => {
    const heard: string[] = [];
    function listener(e: Event) {
      const detail = (e as CustomEvent<string>).detail;
      if (typeof detail === "string") heard.push(detail);
    }
    window.addEventListener("gowork:aria-announce", listener);
    try {
      const { rerender } = render(<Chapter04TheWall progress={0.05} />);
      const baseline = heard.length;
      act(() => {
        rerender(<Chapter04TheWall progress={0.3} />);
      });
      act(() => {
        rerender(<Chapter04TheWall progress={0.6} />);
      });
      act(() => {
        rerender(<Chapter04TheWall progress={0.9} />);
      });
      // 4 sub-chapter entries → at least 4 narration events
      expect(heard.length - baseline).toBeGreaterThanOrEqual(3);
    } finally {
      window.removeEventListener("gowork:aria-announce", listener);
    }
  });

  it("renders the locked editorial detail at every step", () => {
    const expectedDetails: Record<string, string> = {
      "4a": "4.8 miles",
      "4b": "45 minutes",
      "4c": "$1,200",
      "4d": "one in three",
    };
    const { rerender } = render(<Chapter04TheWall progress={STEPS[0].progress} />);
    for (const step of STEPS) {
      act(() => {
        rerender(<Chapter04TheWall progress={step.progress} />);
      });
      expect(screen.getByTestId("ch4-detail").textContent).toContain(
        expectedDetails[step.expectedSub],
      );
    }
  });
});

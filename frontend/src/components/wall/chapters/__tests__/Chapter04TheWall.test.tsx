/**
 * W2 Driver C — Chapter04TheWall (T2.31) orchestrator.
 *
 * Renders the active sub-chapter based on local progress + announces
 * sub-chapter changes via ARIA-live + emits a sound trigger on entry.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, act } from "@testing-library/react";
import { Chapter04TheWall } from "../Chapter04TheWall";
import { setLocale } from "@/lib/i18n";
import * as soundLib from "@/lib/wall/sound";

describe("Chapter04TheWall — sub-chapter selection", () => {
  beforeEach(() => {
    setLocale("en");
  });

  it("renders 4a at the start of the chapter", () => {
    render(<Chapter04TheWall progress={0.05} />);
    expect(
      screen.getByTestId("ch4-subchapter").getAttribute("data-subchapter"),
    ).toBe("4a");
  });

  it("renders 4b after the first quarter", () => {
    render(<Chapter04TheWall progress={0.3} />);
    expect(
      screen.getByTestId("ch4-subchapter").getAttribute("data-subchapter"),
    ).toBe("4b");
  });

  it("renders 4c around the midpoint", () => {
    render(<Chapter04TheWall progress={0.6} />);
    expect(
      screen.getByTestId("ch4-subchapter").getAttribute("data-subchapter"),
    ).toBe("4c");
  });

  it("renders 4d at the end", () => {
    render(<Chapter04TheWall progress={0.9} />);
    expect(
      screen.getByTestId("ch4-subchapter").getAttribute("data-subchapter"),
    ).toBe("4d");
  });

  it("publishes the chapter wrapper with data-chapter='04'", () => {
    render(<Chapter04TheWall progress={0.1} />);
    expect(
      screen.getByTestId("chapter04-wall").getAttribute("data-chapter"),
    ).toBe("04");
  });
});

describe("Chapter04TheWall — sub-chapter transitions + sound", () => {
  let playSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    playSpy = vi.spyOn(soundLib, "play").mockImplementation(() => undefined);
  });

  afterEach(() => {
    playSpy.mockRestore();
  });

  it("plays a sound on first sub-chapter entry", () => {
    render(<Chapter04TheWall progress={0.05} />);
    expect(playSpy).toHaveBeenCalledWith("paper-rustle");
  });

  it("plays a different sound when the sub-chapter changes", () => {
    const { rerender } = render(<Chapter04TheWall progress={0.05} />);
    playSpy.mockClear();
    rerender(<Chapter04TheWall progress={0.3} />);
    // 4b uses footstep
    expect(playSpy).toHaveBeenCalledWith("footstep");
  });

  it("does NOT replay the same sound when progress changes within a sub-chapter", () => {
    const { rerender } = render(<Chapter04TheWall progress={0.05} />);
    playSpy.mockClear();
    rerender(<Chapter04TheWall progress={0.15} />);
    expect(playSpy).not.toHaveBeenCalled();
  });
});

describe("Chapter04TheWall — ARIA-live narration", () => {
  it("dispatches the sub-chapter aria string on entry", () => {
    const heard: string[] = [];
    function listener(e: Event) {
      const detail = (e as CustomEvent<string>).detail;
      if (typeof detail === "string") heard.push(detail);
    }
    window.addEventListener("gowork:aria-announce", listener);
    try {
      render(<Chapter04TheWall progress={0.05} />);
      // The synchronous useEffect has fired by the time render() returns.
      expect(heard.some((m) => m.includes("Barrier one"))).toBe(true);
    } finally {
      window.removeEventListener("gowork:aria-announce", listener);
    }
  });

  it("dispatches a fresh narration when the sub-chapter changes", () => {
    const heard: string[] = [];
    function listener(e: Event) {
      const detail = (e as CustomEvent<string>).detail;
      if (typeof detail === "string") heard.push(detail);
    }
    window.addEventListener("gowork:aria-announce", listener);
    try {
      const { rerender } = render(<Chapter04TheWall progress={0.05} />);
      heard.length = 0;
      act(() => {
        rerender(<Chapter04TheWall progress={0.6} />);
      });
      expect(heard.some((m) => m.includes("Barrier three"))).toBe(true);
    } finally {
      window.removeEventListener("gowork:aria-announce", listener);
    }
  });
});

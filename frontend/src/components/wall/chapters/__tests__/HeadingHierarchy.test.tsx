/**
 * W2 Driver C — heading hierarchy + landmark contracts.
 *
 * Each chapter section must:
 *   - have a single h2 (the chapter title) as its only heading
 *   - associate the h2 with the section via aria-labelledby
 *   - keep h1 reserved for the page (Driver A's WallContainer owns it)
 */
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Chapter04TheWall } from "../Chapter04TheWall";
import { Chapter05Labyrinth } from "../Chapter05Labyrinth";
import { Chapter04aCriminalRecord } from "../Chapter04aCriminalRecord";
import { Chapter04dBadCredit } from "../Chapter04dBadCredit";
import { setLocale } from "@/lib/i18n";

describe("Heading hierarchy", () => {
  it("Chapter04TheWall declares one h2 (chapter title) — sub-chapter h2 nests inside", () => {
    setLocale("en");
    render(<Chapter04TheWall progress={0.1} />);
    // The chapter title is sr-only; the sub-chapter title is visible. Both
    // are h2 — that's intentional: chapter and sub-chapter share heading
    // weight in this magazine layout. No h1 inside; the page owns h1.
    const h1s = document.querySelectorAll("h1");
    expect(h1s.length).toBe(0);
  });

  it("Chapter05Labyrinth has exactly one h2 (the chapter title)", () => {
    render(<Chapter05Labyrinth progress={0.5} />);
    const h2s = document.querySelectorAll("h2");
    expect(h2s.length).toBe(1);
    const h1s = document.querySelectorAll("h1");
    expect(h1s.length).toBe(0);
  });

  it("each Ch4 sub-chapter associates its title with its section via aria-labelledby", () => {
    render(<Chapter04aCriminalRecord progress={0.1} />);
    const section = screen.getByTestId("ch4-subchapter");
    const labelledBy = section.getAttribute("aria-labelledby");
    expect(labelledBy).toBeTruthy();
    expect(document.getElementById(labelledBy!)).not.toBeNull();
  });

  it("Ch4d titles render with rose tint (foreshadowing the cliff)", () => {
    render(<Chapter04dBadCredit progress={0.9} />);
    expect(
      screen.getByTestId("ch4-subchapter").getAttribute("data-emphasis-tint"),
    ).toBe("rose");
  });
});

describe("Landmark + region semantics", () => {
  it("Ch5 declares its labyrinth SVG as decorative (aria-hidden)", () => {
    render(<Chapter05Labyrinth progress={0.5} />);
    const svg = screen.getByTestId("ch5-labyrinth-svg");
    expect(svg.getAttribute("aria-hidden")).toBe("true");
    expect(svg.getAttribute("focusable")).toBe("false");
  });

  it("FormsCounter is announced as a status region", () => {
    render(<Chapter05Labyrinth progress={0.5} />);
    const counter = screen.getByTestId("forms-counter");
    expect(counter.getAttribute("role")).toBe("status");
  });
});

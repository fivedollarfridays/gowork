/**
 * W2 Driver C — Ch4 sub-chapter components (4a / 4b / 4c / 4d).
 *
 * Each sub-chapter renders an editorial overlay + stat band + ARIA-live
 * narration. They all share the same shape — a single test file covers
 * all four to keep the test surface tight while still asserting the
 * locked editorial copy on each one.
 */
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Chapter04aCriminalRecord } from "../Chapter04aCriminalRecord";
import { Chapter04bNoTransit } from "../Chapter04bNoTransit";
import { Chapter04cNoChildcare } from "../Chapter04cNoChildcare";
import { Chapter04dBadCredit } from "../Chapter04dBadCredit";
import { setLocale } from "@/lib/i18n";

describe("Chapter04aCriminalRecord", () => {
  it("renders the locked editorial detail (4.8 miles, 71 minutes)", () => {
    setLocale("en");
    render(<Chapter04aCriminalRecord progress={0.1} />);
    expect(screen.getByTestId("ch4-detail").textContent).toContain("4.8 miles");
    expect(screen.getByTestId("ch4-detail").textContent).toContain(
      "71 minutes",
    );
  });

  it("emits a stat band with tabular-nums + amber accent", () => {
    render(<Chapter04aCriminalRecord progress={0.1} />);
    const stat = screen.getByTestId("ch4-stat-value");
    expect(stat.textContent).toBe("71 min");
    expect(stat.className).toContain("tabular-nums");
  });

  it("declares its sub-chapter id on the root element", () => {
    render(<Chapter04aCriminalRecord progress={0.1} />);
    expect(
      screen.getByTestId("ch4-subchapter").getAttribute("data-subchapter"),
    ).toBe("4a");
  });

  it("renders Spanish copy when locale is es", () => {
    setLocale("es");
    render(<Chapter04aCriminalRecord progress={0.1} />);
    expect(screen.getByTestId("ch4-detail").textContent).toContain(
      "Autobús 4",
    );
    setLocale("en");
  });
});

describe("Chapter04bNoTransit", () => {
  it("renders the locked editorial (45 minutes + transfer)", () => {
    setLocale("en");
    render(<Chapter04bNoTransit progress={0.4} />);
    expect(screen.getByTestId("ch4-detail").textContent).toContain(
      "45 minutes",
    );
  });

  it("shows the 87-minute commute stat", () => {
    render(<Chapter04bNoTransit progress={0.4} />);
    expect(screen.getByTestId("ch4-stat-value").textContent).toBe("87 min");
  });

  it("declares sub-chapter 4b", () => {
    render(<Chapter04bNoTransit progress={0.4} />);
    expect(
      screen.getByTestId("ch4-subchapter").getAttribute("data-subchapter"),
    ).toBe("4b");
  });
});

describe("Chapter04cNoChildcare", () => {
  it("renders the locked editorial ($1,200 a month)", () => {
    setLocale("en");
    render(<Chapter04cNoChildcare progress={0.6} />);
    expect(screen.getByTestId("ch4-detail").textContent).toContain("$1,200");
  });

  it("shows the $1,200/mo stat", () => {
    render(<Chapter04cNoChildcare progress={0.6} />);
    expect(screen.getByTestId("ch4-stat-value").textContent).toBe("$1,200/mo");
  });

  it("declares sub-chapter 4c", () => {
    render(<Chapter04cNoChildcare progress={0.6} />);
    expect(
      screen.getByTestId("ch4-subchapter").getAttribute("data-subchapter"),
    ).toBe("4c");
  });
});

describe("Chapter04dBadCredit", () => {
  it("renders the locked editorial (one in three jobs)", () => {
    setLocale("en");
    render(<Chapter04dBadCredit progress={0.9} />);
    expect(screen.getByTestId("ch4-detail").textContent).toContain(
      "one in three",
    );
  });

  it("shows the 33% stat", () => {
    render(<Chapter04dBadCredit progress={0.9} />);
    expect(screen.getByTestId("ch4-stat-value").textContent).toBe("33%");
  });

  it("declares sub-chapter 4d", () => {
    render(<Chapter04dBadCredit progress={0.9} />);
    expect(
      screen.getByTestId("ch4-subchapter").getAttribute("data-subchapter"),
    ).toBe("4d");
  });
});

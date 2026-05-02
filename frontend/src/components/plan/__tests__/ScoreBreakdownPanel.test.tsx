import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ScoreBreakdownPanel } from "../ScoreBreakdownPanel";
import type { ScoreBreakdown } from "@/lib/types";

const BREAKDOWN: ScoreBreakdown = {
  skills: 0.55,
  title_family: 0.80,
  industry: 0.70,
  years: 0.40,
  education: 0.20,
  certifications: 0.60,
  industry_aligned: true,
};

describe("ScoreBreakdownPanel", () => {
  it("renders the toggle button collapsed by default", () => {
    render(<ScoreBreakdownPanel breakdown={BREAKDOWN} totalScore={0.65} />);
    const btn = screen.getByRole("button", { name: /Why this match/ });
    expect(btn.getAttribute("aria-expanded")).toBe("false");
    // Factor names should NOT be rendered until expanded
    expect(screen.queryByText("Title family")).toBeNull();
  });

  it("expands to show every factor and weight when clicked", () => {
    render(<ScoreBreakdownPanel breakdown={BREAKDOWN} totalScore={0.65} />);
    fireEvent.click(screen.getByRole("button", { name: /Why this match/ }));
    expect(screen.getByText("Skills")).toBeTruthy();
    expect(screen.getByText("Title family")).toBeTruthy();
    expect(screen.getByText("Industry")).toBeTruthy();
    expect(screen.getByText("Experience")).toBeTruthy();
    expect(screen.getByText("Education")).toBeTruthy();
    expect(screen.getByText("Certifications")).toBeTruthy();
  });

  it("renders the headline percentage from totalScore", () => {
    render(<ScoreBreakdownPanel breakdown={BREAKDOWN} totalScore={0.83} />);
    expect(screen.getByRole("button", { name: /83%/ })).toBeTruthy();
  });

  it("notes industry alignment when industry_aligned is true", () => {
    render(<ScoreBreakdownPanel breakdown={BREAKDOWN} totalScore={0.65} />);
    fireEvent.click(screen.getByRole("button", { name: /Why this match/ }));
    expect(screen.getByText(/Industry-aligned/)).toBeTruthy();
  });

  it("notes the mismatch dampener when industry_aligned is false", () => {
    const misaligned: ScoreBreakdown = { ...BREAKDOWN, industry_aligned: false };
    render(<ScoreBreakdownPanel breakdown={misaligned} totalScore={0.45} />);
    fireEvent.click(screen.getByRole("button", { name: /Why this match/ }));
    expect(screen.getByText(/Industry mismatch dampener/)).toBeTruthy();
  });

  it("shows the composite contribution sum", () => {
    render(<ScoreBreakdownPanel breakdown={BREAKDOWN} totalScore={0.65} />);
    fireEvent.click(screen.getByRole("button", { name: /Why this match/ }));
    expect(screen.getByText("Composite")).toBeTruthy();
  });

  it("renders progressbars with valid aria values", () => {
    render(<ScoreBreakdownPanel breakdown={BREAKDOWN} totalScore={0.65} />);
    fireEvent.click(screen.getByRole("button", { name: /Why this match/ }));
    const bars = screen.getAllByRole("progressbar");
    expect(bars.length).toBe(6);
    // All bars must have aria-valuenow in [0,100]
    bars.forEach((b) => {
      const v = Number(b.getAttribute("aria-valuenow"));
      expect(v).toBeGreaterThanOrEqual(0);
      expect(v).toBeLessThanOrEqual(100);
    });
  });
});

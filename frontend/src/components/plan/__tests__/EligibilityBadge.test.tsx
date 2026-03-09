import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { EligibilityBadge } from "../EligibilityBadge";

describe("EligibilityBadge", () => {
  it("renders 'Likely eligible' for likely status", () => {
    render(<EligibilityBadge status="likely" />);
    expect(screen.getByText("Likely eligible")).toBeDefined();
  });

  it("renders 'Check eligibility' for check status", () => {
    render(<EligibilityBadge status="check" />);
    expect(screen.getByText("Check eligibility")).toBeDefined();
  });

  it("renders nothing for null status", () => {
    const { container } = render(<EligibilityBadge status={null} />);
    expect(container.innerHTML).toBe("");
  });

  it("renders nothing for undefined status", () => {
    const { container } = render(<EligibilityBadge status={undefined} />);
    expect(container.innerHTML).toBe("");
  });

  it("applies success styling for likely status", () => {
    render(<EligibilityBadge status="likely" />);
    const badge = screen.getByText("Likely eligible");
    expect(badge.className).toContain("bg-success");
  });

  it("applies warning styling for check status", () => {
    render(<EligibilityBadge status="check" />);
    const badge = screen.getByText("Check eligibility");
    expect(badge.className).toContain("bg-warning");
  });
});

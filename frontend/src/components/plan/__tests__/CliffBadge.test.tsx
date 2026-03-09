import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { CliffBadge } from "../CliffBadge";
import type { CliffImpact } from "@/lib/types";

function impact(overrides: Partial<CliffImpact> = {}): CliffImpact {
  return {
    benefits_change: 0,
    net_monthly_change: 500,
    has_cliff: false,
    severity: null,
    affected_programs: [],
    ...overrides,
  };
}

describe("CliffBadge", () => {
  it("renders nothing when no cliff_impact", () => {
    const { container } = render(<CliffBadge cliffImpact={null} />);
    expect(container.firstChild).toBeNull();
  });

  it("renders safe badge when no cliff", () => {
    render(<CliffBadge cliffImpact={impact()} />);
    expect(screen.getByText(/no benefits impact/i)).toBeInTheDocument();
  });

  it("renders cliff warning with loss amount", () => {
    render(
      <CliffBadge
        cliffImpact={impact({
          has_cliff: true,
          benefits_change: -400,
          severity: "severe",
          affected_programs: ["Section_8"],
        })}
      />,
    );
    expect(screen.getByText(/-\$400\/mo/)).toBeInTheDocument();
  });

  it("shows affected programs", () => {
    render(
      <CliffBadge
        cliffImpact={impact({
          has_cliff: true,
          benefits_change: -228,
          severity: "severe",
          affected_programs: ["SNAP", "Section_8"],
        })}
      />,
    );
    expect(screen.getByText(/SNAP/)).toBeInTheDocument();
    expect(screen.getByText(/Section 8/)).toBeInTheDocument();
  });

  it("shows net monthly change", () => {
    render(
      <CliffBadge
        cliffImpact={impact({ net_monthly_change: 200 })}
      />,
    );
    expect(screen.getByText(/\+\$200\/mo/)).toBeInTheDocument();
  });

  it("shows negative net change", () => {
    render(
      <CliffBadge
        cliffImpact={impact({
          has_cliff: true,
          benefits_change: -500,
          severity: "severe",
          net_monthly_change: -100,
          affected_programs: ["Section_8"],
        })}
      />,
    );
    expect(screen.getByText(/-\$100\/mo vs current/)).toBeInTheDocument();
  });
});

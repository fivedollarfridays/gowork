import { render, screen } from "@testing-library/react";
import { EvidenceChips } from "../EvidenceChips";
import type { EvidenceSource } from "@/lib/types";

const sampleEvidence: EvidenceSource[] = [
  { name: "GreenPath Financial", resource_id: 14 },
  { name: "Alabama Career Center", resource_id: 7 },
  { name: "M-Transit" },
];

describe("EvidenceChips", () => {
  it("renders nothing when evidence is undefined", () => {
    const { container } = render(<EvidenceChips />);
    expect(container.innerHTML).toBe("");
  });

  it("renders nothing when evidence is empty", () => {
    const { container } = render(<EvidenceChips evidence={[]} />);
    expect(container.innerHTML).toBe("");
  });

  it("renders source badges for each evidence", () => {
    render(<EvidenceChips evidence={sampleEvidence} />);
    expect(screen.getByText("GreenPath Financial")).toBeInTheDocument();
    expect(screen.getByText("Alabama Career Center")).toBeInTheDocument();
    expect(screen.getByText("M-Transit")).toBeInTheDocument();
  });

  it("has accessible label", () => {
    render(<EvidenceChips evidence={sampleEvidence} />);
    expect(screen.getByLabelText("Source evidence")).toBeInTheDocument();
  });

  it("renders heading", () => {
    render(<EvidenceChips evidence={sampleEvidence} />);
    expect(screen.getByText("Sources")).toBeInTheDocument();
  });
});

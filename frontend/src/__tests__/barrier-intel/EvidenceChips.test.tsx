import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { EvidenceChips } from "@/components/barrier-intel/EvidenceChips";

describe("EvidenceChips", () => {
  it("renders a chip for each source", () => {
    render(<EvidenceChips sources={["Childcare Playbook", "Family Resource #3"]} />);
    expect(screen.getByText("Childcare Playbook")).toBeInTheDocument();
    expect(screen.getByText("Family Resource #3")).toBeInTheDocument();
  });

  it("renders nothing when sources is empty", () => {
    const { container } = render(<EvidenceChips sources={[]} />);
    expect(container).toBeEmptyDOMElement();
  });
});

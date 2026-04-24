import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { DocumentPreview } from "@/components/documents/DocumentPreview";

describe("DocumentPreview", () => {
  it("renders empty placeholder when no markdown is provided", () => {
    render(
      <DocumentPreview
        markdown={null}
        emptyText="Generate a resume to see the preview."
      />,
    );
    expect(
      screen.getByText(/generate a resume to see the preview/i),
    ).toBeInTheDocument();
  });

  it("renders the raw markdown in a <pre> block when markdown is present", () => {
    const md = "# Resume\n\nStrong worker with 5 years of experience.";
    render(<DocumentPreview markdown={md} emptyText="-" />);
    const pre = screen.getByTestId("document-preview-body");
    expect(pre.tagName).toBe("PRE");
    expect(pre.textContent).toContain("# Resume");
    expect(pre.textContent).toContain("5 years of experience");
  });

  it("exposes role=region with aria-label for a11y", () => {
    render(
      <DocumentPreview
        markdown="Content here."
        emptyText="-"
        ariaLabel="Document preview"
      />,
    );
    const region = screen.getByRole("region", { name: /document preview/i });
    expect(region).toBeInTheDocument();
  });
});

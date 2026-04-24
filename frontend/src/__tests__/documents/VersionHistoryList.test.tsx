import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { VersionHistoryList } from "@/components/documents/VersionHistoryList";
import type { DocumentVersion } from "@/lib/api/documents";

const baseResume: DocumentVersion = {
  version_id: 1,
  session_id: "sess-1",
  doc_type: "resume",
  version_counter: 1,
  generation_method: "template",
  use_counter: 0,
  created_at: "2026-04-20T12:00:00Z",
};

const baseCover: DocumentVersion = {
  version_id: 2,
  session_id: "sess-1",
  doc_type: "cover_letter",
  version_counter: 1,
  generation_method: "llm",
  use_counter: 2,
  created_at: "2026-04-21T12:00:00Z",
};

describe("VersionHistoryList", () => {
  it("shows empty state when there are no versions", () => {
    render(
      <VersionHistoryList
        versions={[]}
        token="tkn"
        docType="resume"
        emptyText="No resume versions yet."
        viewLabel="View"
        pdfLabel="PDF"
        generationBadgeLabels={{ template: "Template", llm: "AI" }}
      />,
    );
    expect(screen.getByText(/no resume versions yet/i)).toBeInTheDocument();
  });

  it("renders one item per resume version with correct PDF + markdown links", () => {
    const versions: DocumentVersion[] = [
      { ...baseResume, version_id: 5, version_counter: 2 },
      { ...baseResume, version_id: 3, version_counter: 1 },
    ];
    render(
      <VersionHistoryList
        versions={versions}
        token="tkn"
        docType="resume"
        emptyText="-"
        viewLabel="View"
        pdfLabel="PDF"
        generationBadgeLabels={{ template: "Template", llm: "AI" }}
      />,
    );
    const items = screen.getAllByRole("listitem");
    expect(items).toHaveLength(2);

    const pdfLinks = screen.getAllByRole("link", { name: /PDF/i });
    expect(pdfLinks[0]).toHaveAttribute(
      "href",
      expect.stringMatching(/\/api\/documents\/resume\/5\/pdf\?token=tkn$/),
    );
  });

  it("filters to cover letters when docType='cover_letter' and uses cover PDF URLs", () => {
    render(
      <VersionHistoryList
        versions={[baseResume, baseCover]}
        token="tkn"
        docType="cover_letter"
        emptyText="-"
        viewLabel="View"
        pdfLabel="PDF"
        generationBadgeLabels={{ template: "Template", llm: "AI" }}
      />,
    );
    const items = screen.getAllByRole("listitem");
    expect(items).toHaveLength(1);
    const pdfLink = screen.getByRole("link", { name: /PDF/i });
    expect(pdfLink).toHaveAttribute(
      "href",
      expect.stringMatching(/\/api\/documents\/cover-letter\/2\/pdf\?token=tkn$/),
    );
  });

  it("renders the generation_method badge with the mapped label", () => {
    render(
      <VersionHistoryList
        versions={[baseCover]}
        token="tkn"
        docType="cover_letter"
        emptyText="-"
        viewLabel="View"
        pdfLabel="PDF"
        generationBadgeLabels={{ template: "Template", llm: "AI" }}
      />,
    );
    expect(screen.getByText("AI")).toBeInTheDocument();
  });

  it("calls onView with the version when the View button is clicked", async () => {
    const { default: userEvent } = await import("@testing-library/user-event");
    const onView = (await import("vitest")).vi.fn();
    render(
      <VersionHistoryList
        versions={[baseResume]}
        token="tkn"
        docType="resume"
        emptyText="-"
        viewLabel="View"
        pdfLabel="PDF"
        generationBadgeLabels={{ template: "Template", llm: "AI" }}
        onView={onView}
      />,
    );
    const viewButton = screen.getByRole("button", { name: /View/i });
    await userEvent.setup().click(viewButton);
    expect(onView).toHaveBeenCalledWith(baseResume);
  });

  it("formats created_at as a readable date string", () => {
    render(
      <VersionHistoryList
        versions={[baseResume]}
        token="tkn"
        docType="resume"
        emptyText="-"
        viewLabel="View"
        pdfLabel="PDF"
        generationBadgeLabels={{ template: "Template", llm: "AI" }}
      />,
    );
    // ISO 2026-04-20 should produce something containing 2026
    expect(screen.getByText(/2026/)).toBeInTheDocument();
  });
});

import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { SuggestedQuestions } from "@/components/barrier-intel/SuggestedQuestions";

describe("SuggestedQuestions", () => {
  it("renders 3 default question chips", () => {
    render(<SuggestedQuestions onSelect={vi.fn()} />);
    expect(screen.getByText("What should I do first to find a job?")).toBeInTheDocument();
    expect(screen.getByText("Why was this plan recommended for me?")).toBeInTheDocument();
    expect(screen.getByText("What's blocking me the most right now?")).toBeInTheDocument();
  });

  it("calls onSelect with question text when chip clicked", () => {
    const onSelect = vi.fn();
    render(<SuggestedQuestions onSelect={onSelect} />);
    fireEvent.click(screen.getByText("What should I do first to find a job?"));
    expect(onSelect).toHaveBeenCalledWith("What should I do first to find a job?");
  });

  it("renders custom questions when provided", () => {
    render(<SuggestedQuestions onSelect={vi.fn()} questions={["Custom Q?"]} />);
    expect(screen.getByText("Custom Q?")).toBeInTheDocument();
  });
});

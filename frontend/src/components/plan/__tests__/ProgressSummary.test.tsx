import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ProgressSummary } from "../ProgressSummary";

describe("ProgressSummary", () => {
  it("renders nothing when total is 0", () => {
    const { container } = render(
      <ProgressSummary completed={0} total={0} />,
    );
    expect(container.innerHTML).toBe("");
  });

  it("shows completion count", () => {
    render(<ProgressSummary completed={3} total={10} />);
    expect(screen.getByText(/3 of 10/)).toBeInTheDocument();
  });

  it("shows completed message when all done", () => {
    render(<ProgressSummary completed={5} total={5} />);
    expect(screen.getByText(/all.*complete/i)).toBeInTheDocument();
  });

  it("has accessible progress bar", () => {
    render(<ProgressSummary completed={2} total={8} />);
    const bar = screen.getByRole("progressbar");
    expect(bar).toBeInTheDocument();
    expect(bar).toHaveAttribute("aria-valuenow", "2");
    expect(bar).toHaveAttribute("aria-valuemax", "8");
  });
});

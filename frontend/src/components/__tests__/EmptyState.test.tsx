import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Briefcase, Search } from "lucide-react";
import { EmptyState } from "../EmptyState";

describe("EmptyState", () => {
  it("renders icon, title, and description", () => {
    render(
      <EmptyState
        icon={Briefcase}
        title="No jobs found"
        description="Try adjusting your search criteria."
      />,
    );
    expect(screen.getByText("No jobs found")).toBeInTheDocument();
    expect(screen.getByText("Try adjusting your search criteria.")).toBeInTheDocument();
  });

  it("renders action button when actionLabel and actionHref provided", () => {
    render(
      <EmptyState
        icon={Search}
        title="Nothing here"
        description="Start a new search."
        actionLabel="Search Again"
        actionHref="/search"
      />,
    );
    const link = screen.getByRole("link", { name: "Search Again" });
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute("href", "/search");
  });

  it("does not render action button when no actionLabel", () => {
    render(
      <EmptyState
        icon={Briefcase}
        title="Empty"
        description="Nothing to show."
      />,
    );
    expect(screen.queryByRole("link")).not.toBeInTheDocument();
  });
});

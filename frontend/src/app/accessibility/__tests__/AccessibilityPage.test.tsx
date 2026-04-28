/**
 * W1 Driver C — accessibility-statement route.
 *
 * Per the dispatch (Wave 7 enrichment), the route is :
 *   - branded (consistent with the wall identity, NOT a default page)
 *   - commits to WCAG 2.1 AA at minimum (with AAA goal noted)
 *   - has a `main#main` landmark for skip-to-content compatibility
 *   - links back to home
 */
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import AccessibilityPage from "../page";

describe("/accessibility — branded a11y statement", () => {
  it("renders a heading naming the statement", () => {
    render(<AccessibilityPage />);
    expect(
      screen.getByRole("heading", { name: /accessibility statement/i }),
    ).toBeInTheDocument();
  });

  it("commits to WCAG 2.1 AA at minimum", () => {
    render(<AccessibilityPage />);
    expect(screen.getByText(/WCAG 2\.1 AA/i)).toBeInTheDocument();
  });

  it("notes WCAG AAA as an aspirational goal", () => {
    render(<AccessibilityPage />);
    expect(screen.getByText(/WCAG 2\.1 AAA|AAA/i)).toBeInTheDocument();
  });

  it("has a main landmark with id=main for skip-to-content compatibility", () => {
    const { container } = render(<AccessibilityPage />);
    expect(container.querySelector("main#main")).toBeInTheDocument();
  });

  it("links back to home", () => {
    render(<AccessibilityPage />);
    const link = screen.getByRole("link", { name: /back to the wall|home/i });
    expect(link).toHaveAttribute("href", "/");
  });
});

import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";

// Mock framer-motion — reduced motion = true so content renders immediately
const mockUseReducedMotion = vi.fn(() => true);
vi.mock("framer-motion", async () => {
  const actual = await vi.importActual("framer-motion");
  return { ...actual, useReducedMotion: () => mockUseReducedMotion() };
});

// Mock next/link
vi.mock("next/link", () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

// Dynamically import Home so mocks are applied
const { default: Home } = await import("../page");

describe("Home page animations", () => {
  it("renders hero heading text", () => {
    render(<Home />);
    expect(
      screen.getByText("What's standing between you and a job?"),
    ).toBeInTheDocument();
  });

  it("renders subtitle about MontGoWork", () => {
    render(<Home />);
    expect(
      screen.getByText(/MontGoWork is a workforce navigator/),
    ).toBeInTheDocument();
  });

  it("renders stat values 20.9, 57.4, and 36K+", () => {
    const { container } = render(<Home />);
    expect(container.textContent).toContain("20.9");
    expect(container.textContent).toContain("57.4");
    expect(container.textContent).toContain("36");
  });

  it("renders How It Works step titles", () => {
    render(<Home />);
    expect(screen.getByText("Assess")).toBeInTheDocument();
    expect(screen.getByText("Match")).toBeInTheDocument();
    expect(screen.getByText("Plan")).toBeInTheDocument();
  });

  it("renders CTA buttons", () => {
    render(<Home />);
    expect(screen.getByText("Get Your Plan")).toBeInTheDocument();
    expect(screen.getByText("Check Credit")).toBeInTheDocument();
  });

  it("renders bottom CTA section", () => {
    render(<Home />);
    expect(screen.getByText("Ready to get started?")).toBeInTheDocument();
  });
});

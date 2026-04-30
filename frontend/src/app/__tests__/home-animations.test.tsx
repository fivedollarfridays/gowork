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

// Mock next/navigation — home page now uses useRouter for the /daily redirect
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn(), back: vi.fn() }),
  useSearchParams: () => new URLSearchParams(),
}));

// W2 (T2.46): the legacy hero/flow/stats landing now lives at /archive.
// `../page` renders WallContainer; the legacy content (which this test
// guards) is preserved verbatim at `../archive/page`. Test the archive
// route so the legacy contract still holds and rollback insurance works.
const { default: Home } = await import("../archive/page");

describe("Archived home page animations (preserved at /archive after W2 T2.46)", () => {
  it("renders hero heading text", () => {
    render(<Home />);
    expect(
      screen.getByText("What's standing between you and a job?"),
    ).toBeInTheDocument();
  });

  it("renders subtitle about GoWork", () => {
    render(<Home />);
    expect(
      screen.getByText(/GoWork is a workforce navigator/),
    ).toBeInTheDocument();
  });

  it("renders Fort Worth stat values (default reference deployment)", () => {
    const { container } = render(<Home />);
    expect(container.textContent).toContain("15.3");
    expect(container.textContent).toContain("64");
    expect(container.textContent).toContain("950");
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

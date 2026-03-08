import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

const mockUseReducedMotion = vi.fn(() => false);
vi.mock("framer-motion", async () => {
  const actual = await vi.importActual("framer-motion");
  return {
    ...actual,
    useReducedMotion: () => mockUseReducedMotion(),
    useScroll: () => ({ scrollYProgress: { get: () => 0, on: vi.fn() } }),
    useSpring: (v: unknown) => v,
  };
});

import { ScrollProgress } from "../ScrollProgress";

beforeEach(() => {
  mockUseReducedMotion.mockReturnValue(false);
});

describe("ScrollProgress", () => {
  it("renders a progress bar element", () => {
    render(<ScrollProgress />);
    expect(screen.getByRole("progressbar")).toBeInTheDocument();
  });

  it("has aria-label attribute", () => {
    render(<ScrollProgress />);
    expect(screen.getByRole("progressbar")).toHaveAttribute(
      "aria-label",
      "Page scroll progress",
    );
  });

  it("has fixed positioning class", () => {
    render(<ScrollProgress />);
    const bar = screen.getByRole("progressbar");
    expect(bar.className).toContain("fixed");
  });

  it("returns null when reduced motion is preferred", () => {
    mockUseReducedMotion.mockReturnValue(true);
    const { container } = render(<ScrollProgress />);
    expect(container.innerHTML).toBe("");
  });
});

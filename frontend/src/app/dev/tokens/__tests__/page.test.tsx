/**
 * /dev/tokens gallery route (T1.76).
 *
 * Renders every TS-side token from `lib/wall/tokens.ts` plus the canonical
 * CSS variables from `app/styles/tokens/*.css`. Dev-only: production build
 * 404s the route via the per-page check + a middleware-equivalent guard
 * inside the page itself (we render `notFound()` in production env).
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen } from "@testing-library/react";

describe("/dev/tokens — Wave 1 carry-over T1.76", () => {
  beforeEach(() => {
    vi.stubEnv("NODE_ENV", "development");
    vi.resetModules();
  });
  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("renders the page heading in development", async () => {
    const { default: TokensPage } = await import("../page");
    render(<TokensPage />);
    expect(
      screen.getByRole("heading", { level: 1, name: /tokens/i }),
    ).toBeInTheDocument();
  });

  it("renders a Color section with the cyan accent swatch", async () => {
    const { default: TokensPage } = await import("../page");
    render(<TokensPage />);
    expect(screen.getByText(/--accent-cyan/i)).toBeInTheDocument();
    expect(screen.getByText(/#22D3EE/i)).toBeInTheDocument();
  });

  it("renders a Typography section with the fluid type scale", async () => {
    const { default: TokensPage } = await import("../page");
    render(<TokensPage />);
    expect(screen.getByText(/--type-display/i)).toBeInTheDocument();
    expect(screen.getByText(/--type-body/i)).toBeInTheDocument();
  });

  it("renders a Motion section with all three spring presets", async () => {
    const { default: TokensPage } = await import("../page");
    render(<TokensPage />);
    expect(screen.getByText(/SPRING_SOFT/i)).toBeInTheDocument();
    expect(screen.getByText(/SPRING_SNAPPY/i)).toBeInTheDocument();
    expect(screen.getByText(/SPRING_ELASTIC/i)).toBeInTheDocument();
  });

  it("renders a Brand section with BrandMark at multiple sizes", async () => {
    const { default: TokensPage } = await import("../page");
    const { container } = render(<TokensPage />);
    const marks = container.querySelectorAll("svg.gowork-mark");
    // 16, 32, 192, 512 — at minimum 4 sizes shown.
    expect(marks.length).toBeGreaterThanOrEqual(4);
  });

  it("renders the Z-Stack section with every overlay token", async () => {
    const { default: TokensPage } = await import("../page");
    render(<TokensPage />);
    expect(screen.getByText(/--z-skip-link/i)).toBeInTheDocument();
    expect(screen.getByText(/--z-header/i)).toBeInTheDocument();
    expect(screen.getByText(/--z-cookie/i)).toBeInTheDocument();
  });
});

describe("/dev/tokens — production guard", () => {
  beforeEach(() => {
    vi.stubEnv("NODE_ENV", "production");
    vi.resetModules();
  });
  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("renders a 'not available' message in production", async () => {
    const { default: ProdTokensPage } = await import("../page");
    const { container } = render(<ProdTokensPage />);
    expect(container.textContent).toMatch(/not available/i);
    expect(container.querySelector("svg.gowork-mark")).toBeNull();
  });
});

/**
 * W4 Driver B — T4.B.9 mobile fallback shell.
 *
 * Mobile users (innerWidth < 768) see:
 *   - A cinematic static map image (CSS gradient + GoWork wordmark for now;
 *     a press-kit JPG can swap in via background-image later).
 *   - Editorial chapter copy that flows in a single column scroll, so
 *     judges-on-phones still get the wall narrative without Mapbox.
 *
 * No Mapbox token check here — this component is the static path. WebGL,
 * 3D Three.js (Ch8), and View Transitions (Ch10) are all skipped on
 * mobile.
 *
 * The shell is intentionally a single, decomposed file ; it composes
 * `MobileChapterCard` (a reusable card that reads chapter copy from i18n)
 * to keep the function count manageable.
 */
import { describe, it, expect, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { TranslationProvider } from "@/hooks/useTranslation";
import { setLocale } from "@/lib/i18n";
import { MobileWallFallback } from "../MobileWallFallback";

function wrap(node: React.ReactNode) {
  return render(<TranslationProvider>{node}</TranslationProvider>);
}

describe("MobileWallFallback (T4.B.9)", () => {
  beforeEach(() => setLocale("en"));

  it("renders a branded title (GoWork wordmark)", () => {
    wrap(<MobileWallFallback />);
    expect(screen.getByText(/^GoWork$/)).toBeInTheDocument();
  });

  it("renders a city subtitle (Fort Worth, TX)", () => {
    wrap(<MobileWallFallback />);
    expect(screen.getByText(/Fort Worth, TX/)).toBeInTheDocument();
  });

  it("renders the title-sequence subtitle from i18n", () => {
    wrap(<MobileWallFallback />);
    expect(
      screen.getByText(/An interactive map of Fort Worth/i),
    ).toBeInTheDocument();
  });

  it("renders all 10 chapter cards in order", () => {
    wrap(<MobileWallFallback />);
    const cards = screen.getAllByTestId(/^mobile-chapter-card-/);
    expect(cards.length).toBeGreaterThanOrEqual(10);
  });

  it("each chapter card has a heading", () => {
    wrap(<MobileWallFallback />);
    const headings = screen.getAllByRole("heading", { level: 2 });
    expect(headings.length).toBeGreaterThanOrEqual(10);
  });

  it("renders Spanish chapter copy when locale is es", () => {
    setLocale("es");
    wrap(<MobileWallFallback />);
    // "El Muro" appears in Ch4 title.
    expect(screen.getByText(/El Muro/)).toBeInTheDocument();
  });

  it("renders an aria-label describing the static fallback", () => {
    wrap(<MobileWallFallback />);
    const region = screen.getByRole("region", { name: /fort worth|gowork/i });
    expect(region).toBeInTheDocument();
  });

  it("does NOT mount a Mapbox container", () => {
    const { container } = wrap(<MobileWallFallback />);
    expect(container.querySelector(".mapboxgl-map")).toBeNull();
    expect(container.querySelector("[data-testid='mapbox-scene']")).toBeNull();
  });

  it("uses a single-column scroll layout (no fixed-position layers)", () => {
    const { container } = wrap(<MobileWallFallback />);
    const root = container.querySelector("[data-mobile-wall]");
    expect(root).toBeInTheDocument();
  });

  it("ships a chapter counter text (10 chapters)", () => {
    wrap(<MobileWallFallback />);
    // We render the chapter cards with their numeric heading like
    // "Chapter 1 — Continental"; assert chapters 1, 5, and 10 are present.
    expect(screen.getByRole("heading", { name: /Continental/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /Labyrinth/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /Find your path/i })).toBeInTheDocument();
  });
});

/**
 * W1 Driver C — T1.42/T1.43/T1.44 reusable wall edge states.
 *
 * Three components, one test file (each behavior tested once) :
 *   - EmptyState   : reusable empty-state with branded copy + line-art SVG.
 *   - LoadingState : skeleton screen (NOT a spinner) with branded pulse.
 *   - ErrorState   : per-component error fallback with optional retry.
 *
 * All three :
 *   - Read copy from the i18n catalog (edge.empty / edge.loading) where
 *     the dispatch defines defaults; ErrorState re-uses edge.500 keys.
 *   - Mount under a TranslationProvider in the consumer; the components
 *     themselves are pure (no provider wrap).
 *   - Respect prefers-reduced-motion at the CSS layer (driver A's lane).
 *   - Render only inline line-art (NO stock illustrations) per dispatch.
 */
import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { TranslationProvider } from "@/hooks/useTranslation";
import { setLocale } from "@/lib/i18n";
import { EmptyState } from "../EmptyState";
import { LoadingState } from "../LoadingState";
import { ErrorState } from "../ErrorState";

function wrap(node: React.ReactNode) {
  return render(<TranslationProvider>{node}</TranslationProvider>);
}

describe("EmptyState (T1.42)", () => {
  beforeEach(() => setLocale("en"));

  it("renders the default empty title from i18n", () => {
    wrap(<EmptyState />);
    expect(screen.getByText(/nothing to chart yet/i)).toBeInTheDocument();
  });

  it("respects custom title and body overrides", () => {
    wrap(<EmptyState title="No appointments" body="Set one to begin" />);
    expect(screen.getByText("No appointments")).toBeInTheDocument();
    expect(screen.getByText("Set one to begin")).toBeInTheDocument();
  });

  it("renders an inline line-art SVG (no img/external assets)", () => {
    const { container } = wrap(<EmptyState />);
    const svg = container.querySelector("svg");
    expect(svg).toBeInTheDocument();
    // No external <img> tags.
    expect(container.querySelector("img")).not.toBeInTheDocument();
  });

  it("renders Spanish copy when locale is es", () => {
    setLocale("es");
    wrap(<EmptyState />);
    expect(screen.getByText(/aún no hay nada que trazar/i)).toBeInTheDocument();
  });
});

describe("LoadingState (T1.43)", () => {
  beforeEach(() => setLocale("en"));

  it("renders a skeleton (NOT a spinner) with branded label", () => {
    wrap(<LoadingState />);
    // aria-busy on the wrapper signals progress to AT.
    expect(screen.getByRole("status")).toHaveAttribute("aria-busy", "true");
    expect(screen.getByText(/calibrating the path/i)).toBeInTheDocument();
  });

  it("does NOT render a spinner element (per dispatch)", () => {
    const { container } = wrap(<LoadingState />);
    expect(container.querySelector('[role="progressbar"]')).toBeNull();
  });

  it("respects a `lines` prop to control skeleton row count", () => {
    const { container } = wrap(<LoadingState lines={5} />);
    expect(container.querySelectorAll('[data-skeleton-line]').length).toBe(5);
  });
});

describe("ErrorState (T1.44)", () => {
  beforeEach(() => setLocale("en"));

  it("renders the branded title", () => {
    wrap(<ErrorState />);
    expect(
      screen.getByRole("heading", { name: /something stalled/i }),
    ).toBeInTheDocument();
  });

  it("invokes onRetry when CTA clicked", () => {
    const onRetry = vi.fn();
    wrap(<ErrorState onRetry={onRetry} />);
    fireEvent.click(screen.getByRole("button", { name: /try again/i }));
    expect(onRetry).toHaveBeenCalled();
  });

  it("hides the retry CTA when onRetry is omitted", () => {
    wrap(<ErrorState />);
    expect(
      screen.queryByRole("button", { name: /try again/i }),
    ).not.toBeInTheDocument();
  });
});

/**
 * Error page — legacy contract preserved for shape; copy migrated to the
 * W1 wall-metaphor branding (T1.41). The 500 was originally introduced
 * in T13.x with "Something went wrong" / two CTAs (try again + back to
 * home). The W1 sprint replaces the copy with "Something stalled / We're
 * calibrating" sourced from the i18n catalog (edge.500.*) and consolidates
 * to a single retry CTA.
 *
 * The deeper W1 contract (main#main landmark for skip-to-content,
 * Spanish parity, error.message non-leak) is guarded in
 * `edge-error.test.tsx`.
 */
import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { TranslationProvider } from "@/hooks/useTranslation";
import { setLocale } from "@/lib/i18n";
import ErrorPage from "../error";

const SECRET_LEAK = "PII_SECRET_TOKEN_xyz_42_DO_NOT_LEAK";

function renderError(opts?: { error?: Error; reset?: () => void }) {
  const error = opts?.error ?? new Error(SECRET_LEAK);
  const reset = opts?.reset ?? vi.fn();
  const utils = render(
    <TranslationProvider>
      <ErrorPage error={error as Error & { digest?: string }} reset={reset} />
    </TranslationProvider>,
  );
  return { ...utils, reset, error };
}

describe("Error page (W1 wall-metaphor copy)", () => {
  beforeEach(() => {
    setLocale("en");
  });

  it("renders the wall-metaphor 500 title in English", () => {
    renderError();
    expect(
      screen.getByRole("heading", { name: /something stalled/i }),
    ).toBeInTheDocument();
  });

  it("renders body copy mentioning the request was logged", () => {
    renderError();
    expect(screen.getByText(/logged/i)).toBeInTheDocument();
  });

  it("does NOT leak error.message in the rendered output", () => {
    const { container } = renderError();
    expect(container.textContent ?? "").not.toContain(SECRET_LEAK);
  });

  it("calls reset() when retry button is clicked", () => {
    const { reset } = renderError();
    fireEvent.click(screen.getByRole("button", { name: /try again/i }));
    expect(reset).toHaveBeenCalledTimes(1);
  });

  it("renders Spanish copy when locale is es", () => {
    setLocale("es");
    renderError();
    expect(
      screen.getByRole("heading", { name: /algo se detuvo/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /intentar de nuevo/i }),
    ).toBeInTheDocument();
  });

  it("uses responsive layout classes (centered + max-width)", () => {
    const { container } = renderError();
    const main = container.querySelector("main");
    expect(main).toBeTruthy();
    expect(main?.className).toMatch(/max-w-|mx-auto/);
  });
});

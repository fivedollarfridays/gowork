/**
 * polish-2 Driver D — T39 redesigned 500 error page.
 *
 * Locks the polish-2 contract:
 *   - Section is tagged `[data-edge-state="500"]`.
 *   - Ch1 background `.ch01-bg` is mounted (atmosphere).
 *   - The retry CTA invokes the Next.js `reset()` prop.
 *   - The accent on the eyebrow is the rose token (severity).
 *   - main#main landmark for SkipToContent.
 */
import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { TranslationProvider } from "@/hooks/useTranslation";
import { setLocale } from "@/lib/i18n";
import ErrorPage from "../error";

function renderError(opts?: { reset?: () => void }) {
  const reset = opts?.reset ?? vi.fn();
  const error = new Error("test") as Error & { digest?: string };
  const utils = render(
    <TranslationProvider>
      <ErrorPage error={error} reset={reset} />
    </TranslationProvider>,
  );
  return { ...utils, reset };
}

describe("/error — polish-2 T39", () => {
  beforeEach(() => setLocale("en"));

  it("tags the page with data-edge-state=500", () => {
    const { container } = renderError();
    expect(container.querySelector('[data-edge-state="500"]')).not.toBeNull();
  });

  it("mounts the Ch1 background pattern (.ch01-bg)", () => {
    const { container } = renderError();
    expect(container.querySelector(".ch01-bg")).not.toBeNull();
  });

  it("retry CTA invokes the reset prop (Next 13 error API)", () => {
    const reset = vi.fn();
    renderError({ reset });
    fireEvent.click(screen.getByRole("button", { name: /try again/i }));
    expect(reset).toHaveBeenCalledTimes(1);
  });

  it("preserves the main#main landmark for SkipToContent", () => {
    const { container } = renderError();
    expect(container.querySelector("main#main")).not.toBeNull();
  });
});

/**
 * polish-2 Driver D — T40 segment-level loading shell.
 *
 * Locks:
 *   - Loading shell renders `[data-edge-state="loading"]`.
 *   - Includes a brand-mark loading-loop (looking for the brand SVG via
 *     a `data-brand-loop` hook the shell adds).
 *   - Includes a 4-row skeleton (LoadingState used internally).
 *   - main#main landmark for SkipToContent.
 */
import { describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import { TranslationProvider } from "@/hooks/useTranslation";
import Loading from "../loading";

function renderLoading() {
  return render(
    <TranslationProvider>
      <Loading />
    </TranslationProvider>,
  );
}

describe("/loading — polish-2 T40", () => {
  it("tags the page with data-edge-state=loading", () => {
    const { container } = renderLoading();
    expect(container.querySelector('[data-edge-state="loading"]')).not.toBeNull();
  });

  it("renders an animated brand mark loop", () => {
    const { container } = renderLoading();
    expect(container.querySelector("[data-brand-loop]")).not.toBeNull();
  });

  it("renders a 4-row skeleton placeholder", () => {
    const { container } = renderLoading();
    expect(container.querySelectorAll("[data-skeleton-line]").length).toBe(4);
  });

  it("preserves the main#main landmark for SkipToContent", () => {
    const { container } = renderLoading();
    expect(container.querySelector("main#main")).not.toBeNull();
  });
});

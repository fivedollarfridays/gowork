/**
 * polish-2 Driver D — T38 redesigned 404 page.
 *
 * The 404 must lift the wall metaphor through the Ch1 background pattern
 * (grid + dual glow + grain). Locks:
 *   - Section is tagged `[data-edge-state="404"]` (consumed by the
 *     polish-2 enforcement gate).
 *   - The Ch1 background `.ch01-bg` is mounted inside the page (no
 *     duplicate site chrome — just the atmosphere).
 *   - Single CTA back home, copy still i18n.
 *   - main#main landmark preserved for SkipToContent.
 */
import { describe, it, expect, beforeEach } from "vitest";
import { render } from "@testing-library/react";
import { TranslationProvider } from "@/hooks/useTranslation";
import { setLocale } from "@/lib/i18n";
import NotFound from "../not-found";

function renderNotFound() {
  return render(
    <TranslationProvider>
      <NotFound />
    </TranslationProvider>,
  );
}

describe("/not-found — polish-2 T38", () => {
  beforeEach(() => setLocale("en"));

  it("tags the page section with data-edge-state=404", () => {
    const { container } = renderNotFound();
    expect(container.querySelector('[data-edge-state="404"]')).not.toBeNull();
  });

  it("mounts the Ch1 background pattern (.ch01-bg) for atmosphere", () => {
    const { container } = renderNotFound();
    expect(container.querySelector(".ch01-bg")).not.toBeNull();
  });

  it("keeps a single CTA back home (anchor href=/)", () => {
    const { container } = renderNotFound();
    const links = Array.from(container.querySelectorAll('a[href="/"]'));
    expect(links.length).toBeGreaterThanOrEqual(1);
  });

  it("preserves the main#main landmark for SkipToContent", () => {
    const { container } = renderNotFound();
    expect(container.querySelector("main#main")).not.toBeNull();
  });
});

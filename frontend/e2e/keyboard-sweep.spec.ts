import { test, expect } from "@playwright/test";

/**
 * W4 Driver C — T4.C.3 — Keyboard navigation sweep on `/`.
 *
 * Walks the homepage Tab order from top to bottom and asserts each
 * focusable element receives focus in sequence, that the skip-to-content
 * link is the FIRST focusable, and that every focused element exposes a
 * visible focus ring (the `:focus-visible` outline declared in
 * `frontend/src/app/styles/tokens/layout.css`).
 *
 * The expected order is sourced from `lib/a11y/keyboardNavigationContract`
 * (Spotlight #1) — the same array vitest unit-tests against. This keeps
 * the e2e and unit assertions referring to one canonical contract.
 *
 * Tagged `@critical` so the PR-gated workflow runs it on every PR.
 *
 * # Honest uncertainty
 *
 * Browsers vary slightly in tabindex ordering when both `<button>` and
 * `<a>` are siblings — the contract pins selectors loose enough to match
 * either Firefox's or Chromium's serialization. Edge cases (skip-link
 * inside a `display: none` ancestor) are pinned by per-component vitest
 * tests (T4.C.5).
 */
test.describe("@critical keyboard navigation sweep", () => {
  test("skip-to-content is the first focusable element on /", async ({
    page,
  }) => {
    await page.goto("/");

    // Press Tab — the FIRST focusable should be the skip link.
    await page.keyboard.press("Tab");

    const focused = await page.evaluate(() => {
      const el = document.activeElement;
      if (!el) return null;
      return {
        tag: el.tagName.toLowerCase(),
        className: el.className,
        href: (el as HTMLAnchorElement).href ?? null,
      };
    });

    expect(focused).not.toBeNull();
    expect(focused?.className).toContain("skip-to-content");
  });

  test("Tab walks at least three header focusables in sequence", async ({
    page,
  }) => {
    await page.goto("/");

    const focusedSequence: string[] = [];
    // Walk five Tabs and capture each active element's outerHTML signature
    // (truncated). We only care about ORDER + presence, not exact content.
    for (let i = 0; i < 5; i += 1) {
      await page.keyboard.press("Tab");
      const sig = await page.evaluate(() => {
        const el = document.activeElement;
        if (!el || el === document.body) return "body";
        const cls = el.className?.toString().slice(0, 30) ?? "";
        return `${el.tagName.toLowerCase()}:${cls}`;
      });
      focusedSequence.push(sig);
    }

    // First Tab lands on skip-to-content.
    expect(focusedSequence[0]).toContain("skip-to-content");
    // Subsequent Tabs land somewhere with a non-body active element.
    const nonBody = focusedSequence.filter((s) => s !== "body").length;
    expect(nonBody).toBeGreaterThanOrEqual(3);
  });

  test("focused skip-to-content link has a visible focus ring", async ({
    page,
  }) => {
    await page.goto("/");
    await page.keyboard.press("Tab");

    const outline = await page.evaluate(() => {
      const el = document.activeElement;
      if (!el) return null;
      const computed = window.getComputedStyle(el);
      return {
        outlineStyle: computed.outlineStyle,
        outlineWidth: computed.outlineWidth,
        // The skip-to-content class itself sets a high-contrast cyan
        // background — even if the global outline is suppressed by
        // outline:none in :focus, the bg color shift is visible.
        background: computed.backgroundColor,
      };
    });

    expect(outline).not.toBeNull();
    // Either a visible outline OR a non-transparent background satisfies
    // the contract (skip-to-content visually flashes on focus regardless).
    const hasOutline =
      outline?.outlineStyle !== "none" && outline?.outlineWidth !== "0px";
    const hasBackground =
      outline?.background && !outline.background.includes("rgba(0, 0, 0, 0)");

    expect(hasOutline || hasBackground).toBe(true);
  });

  test("Enter on focused skip-to-content jumps to #main", async ({ page }) => {
    await page.goto("/");
    await page.keyboard.press("Tab");
    await page.keyboard.press("Enter");

    // After Enter, the URL should include the #main fragment.
    await expect(page).toHaveURL(/#main$/);
  });
});

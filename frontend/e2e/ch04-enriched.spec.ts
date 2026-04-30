/**
 * Driver Ch04-enrich — visual snapshot of the enriched Mapbox section.
 *
 * Runs against a local `next dev` server; loads `/`, scrolls to Ch04,
 * waits for `[data-map-alive="true"]` (or a 3s ceiling — fallback path),
 * then snaps `screenshots/ch04-enriched.png`.
 *
 * To run:
 *   npm run dev               # start server (separate terminal)
 *   npx playwright test ch04-enriched.spec.ts
 */
import { test, expect } from "@playwright/test";

test("Ch04 enriched stack — full visual snapshot @ch04-enrich", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/");

  // Scroll the Ch4 section into view + give the map ~2.5s to mount layers.
  await page.locator("#chapter-04").scrollIntoViewIfNeeded();
  await Promise.race([
    page.waitForSelector('section.ch04[data-map-alive="true"]', { timeout: 3000 }),
    page.waitForTimeout(2500),
  ]);
  // Extra beat for the SVG overlay to project + the route draw-in to
  // settle. Ch04 has 4s cyan + 5s amber draw-in animations.
  await page.waitForTimeout(1500);

  await page.screenshot({
    path: "screenshots/ch04-enriched.png",
    fullPage: false,
    clip: { x: 0, y: 0, width: 1440, height: 900 },
  });

  // Sanity assertions so the test signals failure if the enriched stack
  // didn't paint.
  await expect(page.locator("[data-ch04-svg-overlay]").first()).toBeVisible();
  await expect(page.locator("[data-ch04-compass]").first()).toBeVisible();
  await expect(page.locator("[data-ch04-stat-row]").first()).toBeVisible();
  await expect(page.locator("[data-ch04-attrib]").first()).toBeVisible();
  await expect(page.locator("[data-ch04-legend]").first()).toBeVisible();
});

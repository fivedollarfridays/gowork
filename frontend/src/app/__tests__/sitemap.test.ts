/**
 * T13.117 — Sitemap + robots.txt
 *
 * Pins the structure of `app/sitemap.ts` and `app/robots.ts` so a future
 * regression that, e.g., dumps every worker-only route (which is
 * token-gated and unsafe to enumerate) into the sitemap, or drops the
 * `/admin/` Disallow rule, fails this test instead of shipping to prod.
 *
 * Acceptance criteria pinned:
 *   - /sitemap.xml is valid (object array conforming to Next.js
 *     MetadataRoute.Sitemap)
 *   - /robots.txt is served (object conforming to MetadataRoute.Robots)
 *   - Admin routes disallowed
 */
import { describe, it, expect, beforeAll } from "vitest";

let sitemap: typeof import("../sitemap").default;
let robots: typeof import("../robots").default;

beforeAll(async () => {
  sitemap = (await import("../sitemap")).default;
  robots = (await import("../robots")).default;
});

describe("sitemap.ts", () => {
  it("returns a non-empty array of sitemap entries", () => {
    const entries = sitemap();
    expect(Array.isArray(entries)).toBe(true);
    expect(entries.length).toBeGreaterThan(0);
  });

  it("includes the home route", () => {
    const urls = sitemap().map((e) => e.url);
    expect(urls.some((u) => /\/$/.test(u))).toBe(true);
  });

  it("includes the public /assess discovery route", () => {
    const urls = sitemap().map((e) => e.url);
    expect(urls.some((u) => u.endsWith("/assess"))).toBe(true);
  });

  it("does NOT include token-gated /feedback/ or /shared/ routes", () => {
    const urls = sitemap().map((e) => e.url);
    expect(urls.some((u) => u.includes("/feedback/"))).toBe(false);
    expect(urls.some((u) => u.includes("/shared/"))).toBe(false);
  });

  it("does NOT include admin routes", () => {
    const urls = sitemap().map((e) => e.url);
    expect(urls.some((u) => u.includes("/admin"))).toBe(false);
  });

  it("uses the absolute SITE_URL prefix on every entry", () => {
    const entries = sitemap();
    for (const entry of entries) {
      expect(entry.url).toMatch(/^https?:\/\//);
    }
  });

  it("provides lastModified on every entry", () => {
    const entries = sitemap();
    for (const entry of entries) {
      expect(entry.lastModified).toBeDefined();
    }
  });

  it("home has higher priority than auxiliary routes", () => {
    const entries = sitemap();
    const home = entries.find((e) => /\/$/.test(e.url) && !e.url.endsWith("/assess"));
    expect(home).toBeDefined();
    expect(home!.priority).toBeGreaterThanOrEqual(0.9);
  });

  // polish-2 T52 — chapter anchors + es-locale alts.
  it("includes 8 chapter anchors (?chapter=1..8) for deep-link discovery", () => {
    const urls = sitemap().map((e) => e.url);
    for (let chapter = 1; chapter <= 8; chapter += 1) {
      expect(urls.some((u) => u.endsWith(`/?chapter=${chapter}`))).toBe(true);
    }
  });

  it("home entry declares an es-locale alternate", () => {
    const entries = sitemap();
    const home = entries.find((e) => /\/$/.test(e.url) && !e.url.endsWith("/assess"));
    expect(home?.alternates?.languages?.es).toBeDefined();
  });

  it("each chapter anchor declares an es-locale alternate", () => {
    const entries = sitemap();
    for (let chapter = 1; chapter <= 8; chapter += 1) {
      const entry = entries.find((e) => e.url.endsWith(`/?chapter=${chapter}`));
      expect(entry?.alternates?.languages?.es).toBeDefined();
    }
  });
});

describe("robots.ts", () => {
  it("returns a robots config object", () => {
    const cfg = robots();
    expect(cfg).toBeTypeOf("object");
    expect(Array.isArray(cfg.rules) || typeof cfg.rules === "object").toBe(true);
  });

  it("disallows /admin/ for all user agents (acceptance criterion)", () => {
    const cfg = robots();
    const rulesArr = Array.isArray(cfg.rules) ? cfg.rules : [cfg.rules];
    const wildcardRule = rulesArr.find(
      (r) => r && (r.userAgent === "*" || (Array.isArray(r.userAgent) && r.userAgent.includes("*"))),
    );
    expect(wildcardRule).toBeDefined();
    const disallow = wildcardRule!.disallow;
    const disallowArr = Array.isArray(disallow) ? disallow : disallow ? [disallow] : [];
    expect(disallowArr.some((d) => d.includes("/admin"))).toBe(true);
  });

  it("disallows token-gated /feedback/ and /shared/ from indexing", () => {
    const cfg = robots();
    const rulesArr = Array.isArray(cfg.rules) ? cfg.rules : [cfg.rules];
    const wildcardRule = rulesArr.find(
      (r) => r && (r.userAgent === "*" || (Array.isArray(r.userAgent) && r.userAgent.includes("*"))),
    );
    const disallow = wildcardRule!.disallow;
    const disallowArr = Array.isArray(disallow) ? disallow : disallow ? [disallow] : [];
    expect(disallowArr.some((d) => d.includes("/feedback"))).toBe(true);
    expect(disallowArr.some((d) => d.includes("/shared"))).toBe(true);
  });

  it("disallows /api/ defensively", () => {
    const cfg = robots();
    const rulesArr = Array.isArray(cfg.rules) ? cfg.rules : [cfg.rules];
    const wildcardRule = rulesArr.find(
      (r) => r && (r.userAgent === "*" || (Array.isArray(r.userAgent) && r.userAgent.includes("*"))),
    );
    const disallow = wildcardRule!.disallow;
    const disallowArr = Array.isArray(disallow) ? disallow : disallow ? [disallow] : [];
    expect(disallowArr.some((d) => d.includes("/api"))).toBe(true);
  });

  it("declares an absolute sitemap URL", () => {
    const cfg = robots();
    const sm = cfg.sitemap;
    const smArr = Array.isArray(sm) ? sm : sm ? [sm] : [];
    expect(smArr.length).toBeGreaterThan(0);
    for (const url of smArr) {
      expect(url).toMatch(/^https?:\/\/.+\/sitemap\.xml$/);
    }
  });

  it("allows the root path so the home page can still be crawled", () => {
    const cfg = robots();
    const rulesArr = Array.isArray(cfg.rules) ? cfg.rules : [cfg.rules];
    const wildcardRule = rulesArr.find(
      (r) => r && (r.userAgent === "*" || (Array.isArray(r.userAgent) && r.userAgent.includes("*"))),
    );
    expect(wildcardRule!.allow).toBeDefined();
  });
});

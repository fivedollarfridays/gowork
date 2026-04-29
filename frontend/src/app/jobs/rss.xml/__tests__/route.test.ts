/**
 * polish-2 T52 — /jobs/rss.xml route tests.
 *
 * Verifies the route returns valid RSS 2.0 XML built from the homepage
 * employer registry (`lib/home/employers.ts`).
 */
import { describe, it, expect } from "vitest";
import { GET } from "../route";
import { HOME_EMPLOYERS } from "@/lib/home/employers";

describe("/jobs/rss.xml route (polish-2 T52)", () => {
  it("returns a 200 response", async () => {
    const res = await GET();
    expect(res.status).toBe(200);
  });

  it("declares an XML/RSS content type", async () => {
    const res = await GET();
    const ct = res.headers.get("content-type") ?? "";
    expect(ct).toMatch(/xml/);
  });

  it("body opens with the RSS 2.0 declaration", async () => {
    const res = await GET();
    const body = await res.text();
    expect(body).toMatch(/^<\?xml version="1\.0"/);
    expect(body).toMatch(/<rss version="2\.0"/);
  });

  it("body contains a <channel> with title + link", async () => {
    const res = await GET();
    const body = await res.text();
    expect(body).toMatch(/<channel>/);
    expect(body).toMatch(/<title>/);
    expect(body).toMatch(/<link>/);
  });

  it("emits one <item> per HOME_EMPLOYERS entry", async () => {
    const res = await GET();
    const body = await res.text();
    const itemCount = (body.match(/<item>/g) ?? []).length;
    expect(itemCount).toBe(HOME_EMPLOYERS.length);
  });

  it("each item references the employer name", async () => {
    const res = await GET();
    const body = await res.text();
    for (const employer of HOME_EMPLOYERS) {
      // employer.name contains "—" + an em-dash; the title up through the
      // dash is sufficient to verify the listing made it into the feed.
      const head = employer.name.split(" — ")[0];
      expect(body).toContain(head);
    }
  });

  it("escapes ampersands in titles to satisfy XML parsers", async () => {
    const res = await GET();
    const body = await res.text();
    expect(body).not.toMatch(/&(?!amp;|lt;|gt;|quot;|apos;)/);
  });
});

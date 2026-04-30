/**
 * polish-2 T52 — /jobs/rss.xml route.
 *
 * Emits an RSS 2.0 feed of the homepage hero-employer set
 * (`HOME_EMPLOYERS` — Alcon, BNSF, JE Dunn). Lifted directly from the
 * canonical registry so the feed and the homepage cards never disagree.
 *
 * Why a feed at all? Press-kit + workforce-board scout traffic — RSS is
 * still the lingua franca for "tell me when new jobs land". Cheap to ship
 * and zero ongoing maintenance because the canonical source is one
 * file.
 */
import { HOME_EMPLOYERS } from "@/lib/home/employers";

const SITE_URL =
  process.env.NEXT_PUBLIC_SITE_URL ?? "https://gowork.example";
const FEED_TITLE = "GoWork — Live jobs in Fort Worth";
const FEED_DESCRIPTION =
  "Active openings curated for the GoWork homepage scrollytelling demo.";

function escapeXml(unsafe: string): string {
  return unsafe
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
}

function renderItem(employer: (typeof HOME_EMPLOYERS)[number]): string {
  const link = `${SITE_URL}/assess?employer=${employer.id}`;
  const title = escapeXml(employer.name);
  const description = escapeXml(
    `${employer.wage} · ${employer.shift} · ${employer.address}. ${employer.blurb}`,
  );
  return [
    "  <item>",
    `    <title>${title}</title>`,
    `    <link>${link}</link>`,
    `    <guid isPermaLink="false">gowork-${employer.id}</guid>`,
    `    <description>${description}</description>`,
    "  </item>",
  ].join("\n");
}

function renderFeed(): string {
  const lastBuild = new Date().toUTCString();
  const items = HOME_EMPLOYERS.map(renderItem).join("\n");
  return [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<rss version="2.0">',
    "<channel>",
    `  <title>${escapeXml(FEED_TITLE)}</title>`,
    `  <link>${SITE_URL}/jobs</link>`,
    `  <description>${escapeXml(FEED_DESCRIPTION)}</description>`,
    "  <language>en-US</language>",
    `  <lastBuildDate>${lastBuild}</lastBuildDate>`,
    items,
    "</channel>",
    "</rss>",
  ].join("\n");
}

export async function GET(): Promise<Response> {
  const body = renderFeed();
  return new Response(body, {
    status: 200,
    headers: {
      "content-type": "application/rss+xml; charset=utf-8",
      "cache-control": "public, max-age=3600, stale-while-revalidate=86400",
    },
  });
}

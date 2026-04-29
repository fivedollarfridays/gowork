/**
 * W5 Driver C — T5.C.6 part 4.
 *
 * Walk every Markdown link in the root README.md. For relative paths,
 * the file MUST exist. For absolute http(s) URLs, the URL MUST be a
 * valid format (no syntax check on reachability — we trust the operator
 * during the manual T-1 hour smoke).
 *
 * Why: a broken README link is the lowest-effort credibility hit a
 * judge can find. A 30-second sanity test prevents that.
 */
import { describe, it, expect } from "vitest";
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

const REPO_ROOT = join(process.cwd(), "..");
const README_PATH = join(REPO_ROOT, "README.md");

interface MarkdownLink {
  text: string;
  target: string;
}

function extractMarkdownLinks(md: string): MarkdownLink[] {
  // Matches [text](target) — handles backticks in text, NOT nested brackets.
  // Excludes shield/badge URLs that are img embeds: ![alt](src).
  const re = /(?<!!)\[([^\]]+)\]\(([^)]+)\)/g;
  const out: MarkdownLink[] = [];
  let m: RegExpExecArray | null;
  while ((m = re.exec(md)) !== null) {
    out.push({ text: m[1], target: m[2] });
  }
  return out;
}

describe("README.md — link validator", () => {
  const md = readFileSync(README_PATH, "utf8");
  const links = extractMarkdownLinks(md);

  it("has at least 5 markdown links (README is non-trivial)", () => {
    expect(links.length).toBeGreaterThanOrEqual(5);
  });

  it("every relative path link resolves to an existing file or directory", () => {
    const broken: string[] = [];
    for (const { target } of links) {
      // Skip absolute URLs and pure anchors.
      if (/^[a-z]+:\/\//i.test(target)) continue;
      if (target.startsWith("#")) continue;
      if (target.startsWith("mailto:")) continue;
      // Strip anchor fragment and querystring.
      const path = target.split(/[#?]/)[0];
      if (!path) continue;
      const abs = join(REPO_ROOT, path);
      if (!existsSync(abs)) {
        broken.push(target);
      }
    }
    expect(broken, `Broken README links: ${broken.join(", ")}`).toHaveLength(0);
  });

  it("every absolute http(s) URL has a valid format (parseable)", () => {
    const malformed: string[] = [];
    for (const { target } of links) {
      if (!/^https?:\/\//i.test(target)) continue;
      try {
        // Throws on syntactically invalid URLs.
        // eslint-disable-next-line no-new
        new URL(target);
      } catch {
        malformed.push(target);
      }
    }
    expect(
      malformed,
      `Malformed URLs in README: ${malformed.join(", ")}`,
    ).toHaveLength(0);
  });

  it("does not link to localhost (a leaked dev URL)", () => {
    const localhostLinks = links
      .filter(({ target }) => /localhost|127\.0\.0\.1/i.test(target))
      .map(({ target }) => target);
    // Localhost in code blocks is fine (those aren't markdown links per the
    // regex). This catches `[name](http://localhost:3000)` only.
    expect(
      localhostLinks,
      `Localhost links must not appear in README markdown links: ${localhostLinks.join(", ")}`,
    ).toHaveLength(0);
  });

  it("does not link to file:// URLs (developer environment leak)", () => {
    const fileLinks = links.filter(({ target }) => /^file:\/\//i.test(target));
    expect(fileLinks).toHaveLength(0);
  });
});

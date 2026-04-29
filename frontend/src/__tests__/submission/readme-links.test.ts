/**
 * W5 Driver A — T5.A.7
 *
 * README link validator. Parses the repository README.md, extracts every
 * relative `[text](path)` link, and asserts the linked file (or directory)
 * exists on disk.
 *
 * External links (http, https, mailto) are skipped. Anchor-only links (#frag)
 * are skipped. Image references (`![alt](path)`) are validated alongside text
 * links — if README references `docs/press-kit/screenshots/ch2-...png`, that
 * path must resolve.
 *
 * Placeholder convention: a path ending in `.placeholder` is accepted as a
 * stand-in for an artifact a sibling driver (Driver B) will produce. This
 * guards the contract: README never ships with a broken link, but it can
 * forward-declare a screenshot that hasn't been rendered yet.
 */
import { describe, it, expect } from "vitest";
import { existsSync, readFileSync, statSync } from "node:fs";
import { join, resolve, dirname } from "node:path";

const REPO_ROOT = resolve(__dirname, "..", "..", "..", "..");
const README_PATH = join(REPO_ROOT, "README.md");

interface ParsedLink {
  text: string;
  href: string;
  line: number;
}

function parseReadmeLinks(markdown: string): ParsedLink[] {
  const links: ParsedLink[] = [];
  const lines = markdown.split("\n");
  // Match [text](url) and ![alt](url). Capture the href.
  const linkRe = /!?\[([^\]]*)\]\(([^)]+)\)/g;
  for (let i = 0; i < lines.length; i++) {
    let match: RegExpExecArray | null;
    while ((match = linkRe.exec(lines[i])) !== null) {
      links.push({ text: match[1], href: match[2].trim(), line: i + 1 });
    }
  }
  return links;
}

function isExternal(href: string): boolean {
  return /^(https?:|mailto:|tel:|ftp:)/i.test(href);
}

function isAnchorOnly(href: string): boolean {
  return href.startsWith("#");
}

function stripFragment(href: string): string {
  const i = href.indexOf("#");
  return i === -1 ? href : href.slice(0, i);
}

function isPlaceholder(href: string): boolean {
  return href.endsWith(".placeholder");
}

function resolveLink(href: string): string {
  // README lives at repo root, so every relative href is relative to REPO_ROOT.
  return join(REPO_ROOT, stripFragment(href));
}

describe("README link validator (T5.A.7)", () => {
  it("README.md exists at repo root", () => {
    expect(existsSync(README_PATH)).toBe(true);
  });

  it("README parses to at least one link", () => {
    const md = readFileSync(README_PATH, "utf8");
    const links = parseReadmeLinks(md);
    expect(links.length).toBeGreaterThan(0);
  });

  it("every relative link in README resolves to an existing file or directory", () => {
    const md = readFileSync(README_PATH, "utf8");
    const links = parseReadmeLinks(md);
    const broken: { href: string; line: number; resolved: string }[] = [];
    for (const link of links) {
      if (isExternal(link.href)) continue;
      if (isAnchorOnly(link.href)) continue;
      if (isPlaceholder(link.href)) continue;
      const resolved = resolveLink(link.href);
      if (!existsSync(resolved)) {
        broken.push({ href: link.href, line: link.line, resolved });
      }
    }
    if (broken.length > 0) {
      const msg = broken
        .map((b) => `  line ${b.line}: ${b.href} -> ${b.resolved}`)
        .join("\n");
      throw new Error(`README has ${broken.length} broken link(s):\n${msg}`);
    }
    expect(broken.length).toBe(0);
  });

  it("every README image reference resolves (or is documented placeholder)", () => {
    const md = readFileSync(README_PATH, "utf8");
    const imgRe = /!\[([^\]]*)\]\(([^)]+)\)/g;
    const broken: string[] = [];
    let match: RegExpExecArray | null;
    while ((match = imgRe.exec(md)) !== null) {
      const href = match[2].trim();
      if (isExternal(href)) continue;
      if (isPlaceholder(href)) continue;
      const resolved = resolveLink(href);
      if (!existsSync(resolved)) {
        broken.push(`image '${href}' (alt='${match[1]}') -> ${resolved}`);
      }
    }
    if (broken.length > 0) {
      throw new Error(`README has missing images:\n  ${broken.join("\n  ")}`);
    }
    expect(broken.length).toBe(0);
  });

  it("README opens with a hero question or thesis line", () => {
    const md = readFileSync(README_PATH, "utf8");
    // The locked copy thesis must appear in the first 80 lines.
    const head = md.split("\n").slice(0, 80).join("\n");
    expect(head).toMatch(/standing between you and a job/i);
  });

  it("README references the LICENSE", () => {
    const md = readFileSync(README_PATH, "utf8");
    expect(md).toMatch(/MIT/);
  });
});

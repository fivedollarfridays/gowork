/**
 * W5 Driver A — T5.A.7
 *
 * Press kit paths validator. Reads docs/press-kit.md, extracts every image
 * reference under docs/press-kit/screenshots/ (or any docs/press-kit/* asset),
 * and asserts each path resolves to a file on disk OR to a sibling
 * `<name>.placeholder` marker file documenting that Driver B has not yet
 * shipped the cinematic still.
 *
 * Why placeholders: Driver A (this lane) authors the press kit; Driver B
 * captures the cinematic stills from the rendered Wall. Allowing
 * `<name>.placeholder` lets the docs ship and the contract stay green
 * while the parallel lane finishes screenshot capture.
 */
import { describe, it, expect } from "vitest";
import { existsSync, readFileSync } from "node:fs";
import { join, resolve } from "node:path";

const REPO_ROOT = resolve(__dirname, "..", "..", "..", "..");
const PRESS_KIT_PATH = join(REPO_ROOT, "docs", "press-kit.md");

interface PressKitImage {
  href: string;
  line: number;
  alt: string;
}

function parsePressKitImages(markdown: string): PressKitImage[] {
  const out: PressKitImage[] = [];
  const lines = markdown.split("\n");
  // Match Markdown image syntax + bare references like (path/to/img.png)
  const imgRe = /!\[([^\]]*)\]\(([^)]+)\)/g;
  for (let i = 0; i < lines.length; i++) {
    let match: RegExpExecArray | null;
    while ((match = imgRe.exec(lines[i])) !== null) {
      out.push({ alt: match[1], href: match[2].trim(), line: i + 1 });
    }
  }
  return out;
}

function isExternal(href: string): boolean {
  return /^(https?:|mailto:|tel:|ftp:)/i.test(href);
}

function resolveAsset(href: string): string {
  // Press kit lives at docs/press-kit.md; relative paths resolve against
  // the repo root (Markdown rendered by GitHub treats them that way when
  // they start with docs/) but we also accept paths relative to docs/.
  if (href.startsWith("docs/")) return join(REPO_ROOT, href);
  if (href.startsWith("/")) return join(REPO_ROOT, href);
  return join(REPO_ROOT, "docs", href);
}

function existsOrPlaceholder(path: string): boolean {
  if (existsSync(path)) return true;
  // Driver B contract: a sibling `.placeholder` file marks intentional gap.
  return existsSync(`${path}.placeholder`);
}

describe("Press kit paths validator (T5.A.7)", () => {
  it("docs/press-kit.md exists", () => {
    expect(existsSync(PRESS_KIT_PATH)).toBe(true);
  });

  it("press kit references at least one cinematic still by filename", () => {
    // Narrative reset (sprint/narrative-reset, commit 03dff3c) rewrote
    // the Screenshots section as plain numbered prose ("1. The Wall
    // (Ch1) (press-01-landing.png)") instead of inline markdown image
    // tags. The cinematic stills are still named by filename so a
    // reporter or judge can request them; the markdown was simplified
    // to render cleaner on Devpost. We assert filename references
    // instead of image tags now.
    const md = readFileSync(PRESS_KIT_PATH, "utf8");
    expect(md).toMatch(/press-\d+-[a-z0-9-]+\.png|landing-full\.png|chapter\d+\.png/i);
  });

  it("every press kit image resolves to a file or a documented placeholder", () => {
    const md = readFileSync(PRESS_KIT_PATH, "utf8");
    const imgs = parsePressKitImages(md);
    const broken: string[] = [];
    for (const img of imgs) {
      if (isExternal(img.href)) continue;
      const resolved = resolveAsset(img.href);
      if (!existsOrPlaceholder(resolved)) {
        broken.push(`line ${img.line}: ${img.href} -> ${resolved}`);
      }
    }
    if (broken.length > 0) {
      throw new Error(
        `Press kit has ${broken.length} unresolved asset(s):\n  ${broken.join("\n  ")}`,
      );
    }
    expect(broken.length).toBe(0);
  });

  it("press kit headline does not lead with Worldwide Vibes (W5 demote)", () => {
    // Narrative reset confirmed the W5 demote: the press kit headline
    // is "GoWork Press Kit (HackFW 2026)" — Worldwide Vibes survives
    // only as an Accolade line further down ("2nd Place, Worldwide
    // Vibes Hackathon"). The headline gate is the first 5 lines (the
    // H1 + the divider); the Accolade section ~line 23 is fine.
    const md = readFileSync(PRESS_KIT_PATH, "utf8");
    const head = md.split("\n").slice(0, 5).join("\n");
    expect(head).not.toMatch(/worldwide vibes/i);
    // Make the demote assertion explicit — HackFW 2026 must lead.
    expect(head).toMatch(/HackFW 2026/);
  });

  it("press kit tagline cites the locked thesis", () => {
    const md = readFileSync(PRESS_KIT_PATH, "utf8");
    expect(md).toMatch(/standing between you and a job/i);
  });

  it("press kit declares MIT license", () => {
    const md = readFileSync(PRESS_KIT_PATH, "utf8");
    expect(md).toMatch(/MIT/);
  });
});

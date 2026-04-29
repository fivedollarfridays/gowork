/**
 * W5 Driver A — T5.A.7
 *
 * Devpost submission content validator. Reads docs/devpost-submission.md and
 * asserts every required Devpost form section is present and non-empty.
 *
 * Devpost requires (and judges grade against):
 *   - Project name + tagline
 *   - Full project description
 *   - Inspiration (why we built it)
 *   - What we learned (the meta layer judges love)
 *   - Challenges we ran into (technical honesty)
 *   - Built with (tags — drives discoverability)
 *   - Categories (Reindustrialization is the HackFW track)
 *   - Team members
 */
import { describe, it, expect } from "vitest";
import { existsSync, readFileSync } from "node:fs";
import { join, resolve } from "node:path";

const REPO_ROOT = resolve(__dirname, "..", "..", "..", "..");
const DEVPOST_PATH = join(REPO_ROOT, "docs", "devpost-submission.md");

const REQUIRED_SECTIONS = [
  "Project name",
  "Tagline",
  "Project description",
  "Inspiration",
  "What we learned",
  "Challenges we ran into",
  "Built with",
  "Categories",
  "Team members",
];

const REQUIRED_TAGS = [
  "Next.js",
  "TypeScript",
  "Mapbox",
  "Three.js",
  "FastAPI",
];

const REQUIRED_CATEGORIES = ["Reindustrialization", "Workforce", "Civic Tech"];

describe("Devpost submission content validator (T5.A.7)", () => {
  it("docs/devpost-submission.md exists", () => {
    expect(existsSync(DEVPOST_PATH)).toBe(true);
  });

  it.each(REQUIRED_SECTIONS)("contains required section: %s", (section) => {
    const md = readFileSync(DEVPOST_PATH, "utf8");
    // Section headers can appear as ## Section, **Section:**, or Section:.
    const re = new RegExp(
      `(^|\\n)\\s*(##+\\s*${section}|\\*\\*${section}[:\\*]|${section}\\s*:)`,
      "i",
    );
    expect(md).toMatch(re);
  });

  it.each(REQUIRED_TAGS)("declares tag/built-with: %s", (tag) => {
    const md = readFileSync(DEVPOST_PATH, "utf8");
    expect(md).toMatch(new RegExp(tag.replace(/\./g, "\\."), "i"));
  });

  it.each(REQUIRED_CATEGORIES)("declares category: %s", (category) => {
    const md = readFileSync(DEVPOST_PATH, "utf8");
    expect(md).toMatch(new RegExp(category, "i"));
  });

  it("declares team: PairCoder + Claude AI", () => {
    const md = readFileSync(DEVPOST_PATH, "utf8");
    expect(md).toMatch(/PairCoder/i);
    expect(md).toMatch(/Claude/i);
  });

  it("references the locked copy thesis", () => {
    const md = readFileSync(DEVPOST_PATH, "utf8");
    expect(md).toMatch(/standing between you and a job|workforce infrastructure/i);
  });

  it("references Fort Worth as the reference deployment", () => {
    const md = readFileSync(DEVPOST_PATH, "utf8");
    expect(md).toMatch(/Fort Worth/i);
  });
});

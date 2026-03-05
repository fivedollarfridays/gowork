import { describe, it, expect } from "vitest";
import fs from "fs";
import path from "path";

const SRC_DIR = path.resolve(__dirname, "..");
const FRONTEND_ROOT = path.resolve(SRC_DIR, "..");

function readFile(fromRoot: string): string {
  return fs.readFileSync(path.resolve(FRONTEND_ROOT, fromRoot), "utf-8");
}

/**
 * Recursively find all .tsx/.ts files in src/, excluding node_modules and __tests__.
 */
function findSourceFiles(dir: string, ext: string[]): string[] {
  const results: string[] = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory() && !entry.name.startsWith("__") && entry.name !== "ui") {
      results.push(...findSourceFiles(full, ext));
    } else if (entry.isFile() && ext.some((e) => entry.name.endsWith(e))) {
      results.push(full);
    }
  }
  return results;
}

describe("Color palette tokens in globals.css", () => {
  const css = readFile("src/app/globals.css");

  it("defines --success variable in :root", () => {
    expect(css).toContain("--success:");
  });

  it("defines --success-foreground variable in :root", () => {
    expect(css).toContain("--success-foreground:");
  });

  it("defines --warning variable in :root", () => {
    expect(css).toContain("--warning:");
  });

  it("defines --warning-foreground variable in :root", () => {
    expect(css).toContain("--warning-foreground:");
  });
});

describe("Color palette tokens in tailwind.config.ts", () => {
  const config = readFile("tailwind.config.ts");

  it("has success color token", () => {
    expect(config).toContain("success");
    expect(config).toContain("hsl(var(--success))");
  });

  it("has warning color token", () => {
    expect(config).toContain("warning");
    expect(config).toContain("hsl(var(--warning))");
  });
});

describe("STATUS_BADGE_STYLES uses semantic tokens", () => {
  const constants = readFile("src/lib/constants.ts");

  it("positive style uses success token", () => {
    expect(constants).toContain("bg-success");
    expect(constants).toContain("text-success");
  });

  it("warning style uses warning token", () => {
    expect(constants).toContain("bg-warning");
  });

  it("negative style uses destructive token", () => {
    expect(constants).toContain("bg-destructive");
    expect(constants).toContain("text-destructive");
  });

  it("does NOT use hardcoded green/amber/red in badge styles", () => {
    // Extract only the STATUS_BADGE_STYLES block
    const match = constants.match(/STATUS_BADGE_STYLES\s*=\s*\{[\s\S]+?\}\s*as\s*const/);
    expect(match).toBeTruthy();
    const block = match![0];
    expect(block).not.toMatch(/text-green-/);
    expect(block).not.toMatch(/text-amber-/);
    expect(block).not.toMatch(/text-red-/);
    expect(block).not.toMatch(/bg-green-/);
    expect(block).not.toMatch(/bg-amber-/);
    expect(block).not.toMatch(/bg-red-/);
  });
});

describe("No hardcoded color classes in application source files", () => {
  // Forbidden patterns: text-red-*, bg-red-*, text-green-*, bg-green-*,
  // text-amber-*, bg-amber-*, bg-yellow-*, text-blue-*, bg-blue-*
  const FORBIDDEN_PATTERN =
    /(?:text|bg|border)-(?:red|green|amber|yellow|blue)-\d+/;

  const sourceFiles = findSourceFiles(
    path.resolve(FRONTEND_ROOT, "src"),
    [".tsx", ".ts"],
  ).filter(
    (f) =>
      !f.includes("node_modules") &&
      !f.includes("__tests__") &&
      !f.includes(".test.") &&
      // Exclude shadcn/ui base components (they use their own tokens)
      !f.includes("/components/ui/"),
  );

  it("found source files to check", () => {
    expect(sourceFiles.length).toBeGreaterThan(0);
  });

  for (const file of sourceFiles) {
    const relPath = path.relative(FRONTEND_ROOT, file);
    it(`${relPath} has no hardcoded color classes`, () => {
      const content = fs.readFileSync(file, "utf-8");
      const lines = content.split("\n");
      const violations: string[] = [];
      for (let i = 0; i < lines.length; i++) {
        const match = lines[i].match(FORBIDDEN_PATTERN);
        if (match) {
          violations.push(`  L${i + 1}: ${match[0]} in "${lines[i].trim()}"`);
        }
      }
      expect(violations).toEqual([]);
    });
  }
});

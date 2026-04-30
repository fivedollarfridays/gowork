/**
 * polish-2 Driver D — T47 chapter-thumbs build script smoke test.
 *
 * Asserts:
 *   - Script exists at the expected path.
 *   - Exports `planChapterThumbs(srcs)` which produces the expected
 *     200w/400w/800w × {webp, avif} output plan for each input JPG.
 *
 * NOTE: We dispatch a Node child process to import the .mjs module.
 * vitest's Vite-driven loader chokes on runtime-constructed URLs to
 * .mjs files on Windows (CRLF line endings); the child-process
 * round-trip runs the script under the same Node version as production.
 */
import { describe, it, expect } from "vitest";
import fs from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";

const FRONTEND_ROOT = path.resolve(__dirname, "..", "..");
const SCRIPT = path.resolve(FRONTEND_ROOT, "scripts/build-chapter-thumbs.mjs");
const SCRIPT_URL = `file:///${SCRIPT.replace(/\\/g, "/")}`;

function runHelper(body: string): unknown {
  const code = `import("${SCRIPT_URL}").then(async (m) => { ${body} }).catch((e) => { console.error(e); process.exit(1); });`;
  const out = execFileSync(
    process.execPath,
    ["--input-type=module", "-e", code],
    { encoding: "utf-8" },
  );
  return JSON.parse(out.trim());
}

describe("polish-2 T47 — chapter-thumbs build script", () => {
  it("the build script exists", () => {
    expect(fs.existsSync(SCRIPT)).toBe(true);
  });

  it("exports planChapterThumbs(srcs) returning 6 variants per input", () => {
    const out = runHelper(
      `const plan = m.planChapterThumbs([
        "/abs/path/01-hero.jpg",
        "/abs/path/02-the-numbers.jpg",
      ]);
      console.log(JSON.stringify(plan));`,
    ) as Array<{ dest: string; width: number; format: string }>;

    expect(out.length).toBe(12);
    for (const p of out) {
      expect(typeof p.dest).toBe("string");
      expect([200, 400, 800]).toContain(p.width);
      expect(["webp", "avif"]).toContain(p.format);
    }
  });

  it("produces destination paths preserving the input basename", () => {
    const out = runHelper(
      `console.log(JSON.stringify(m.planChapterThumbs(["/x/01-hero.jpg"])));`,
    ) as Array<{ dest: string }>;
    const names = out.map((p) => path.basename(p.dest)).sort();
    expect(names).toEqual([
      "01-hero-200.avif",
      "01-hero-200.webp",
      "01-hero-400.avif",
      "01-hero-400.webp",
      "01-hero-800.avif",
      "01-hero-800.webp",
    ]);
  });
});

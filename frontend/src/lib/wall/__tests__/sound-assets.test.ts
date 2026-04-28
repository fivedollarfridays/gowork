import { describe, it, expect } from "vitest";
import { existsSync, statSync } from "node:fs";
import { resolve } from "node:path";

const REPO_ROOT = resolve(__dirname, "../../../../");
const SOUNDS_DIR = resolve(REPO_ROOT, "public/sounds");
const REQUIRED = [
  "footstep.mp3",
  "paper-rustle.mp3",
  "calculator-click.mp3",
  "chime.mp3",
  "wind-ambient.mp3",
];
const MAX_BYTES = 50 * 1024; // 50 KB per asset (T1.57 spec)

describe("sound asset directory (T1.57)", () => {
  it("exists at public/sounds/", () => {
    expect(existsSync(SOUNDS_DIR)).toBe(true);
  });

  it.each(REQUIRED)("has placeholder %s", (file) => {
    const path = resolve(SOUNDS_DIR, file);
    expect(existsSync(path)).toBe(true);
  });

  it.each(REQUIRED)("placeholder %s is <50 KB", (file) => {
    const path = resolve(SOUNDS_DIR, file);
    const stats = statSync(path);
    expect(stats.size).toBeLessThan(MAX_BYTES);
  });

  it("documents replacement requirements in README.md", () => {
    const readmePath = resolve(SOUNDS_DIR, "README.md");
    expect(existsSync(readmePath)).toBe(true);
  });
});

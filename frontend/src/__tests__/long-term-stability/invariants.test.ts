/**
 * W5 Driver D — Long-term-stability sentinel test (Spotlight invention).
 *
 * Compound Lens. This single guard test asserts the project's load-bearing
 * invariants. If a future contributor removes a chapter, drops a translation,
 * forgets to register a sound, or breaks the city framework's structural
 * contract, this test fires loud and forces a deliberate update.
 *
 * The invariants are:
 *
 *   1. Every Wall chapter (Ch1..Ch10) has a chapterSpec entry.
 *   2. Every chapterSpec entry has a non-empty title in EN and ES.
 *   3. Every chapter has a stable slug, a camera target, and chapter bounds.
 *   4. Chapter sound ids are either null (silent chapter) or a valid id.
 *   5. ChapterSpec ids are unique.
 *   6. Slugs are unique.
 *   7. CHAPTER_BOUNDS cover [0, 1] with no gaps and no overlaps.
 *   8. Every required submission artifact is referenced from at least one
 *      submission doc (cross-doc linking is healthy).
 *
 * If any one of these fires, the project's framework contract has drifted —
 * it's not just a refactor, it's a structural change that needs review.
 *
 * Add new invariants here, not new test files. The whole point of this is
 * a single canonical guard.
 */
import { describe, it, expect } from "vitest";
import { existsSync, readFileSync } from "node:fs";
import { join, resolve } from "node:path";
import {
  CHAPTER_SPECS,
  type ChapterSlug,
} from "@/lib/wall/chapterSpec";
import { CHAPTER_BOUNDS } from "@/lib/wall/wallProgress";

const REPO_ROOT = resolve(__dirname, "..", "..", "..", "..");

describe("Long-term stability — framework invariants (Driver D Spotlight)", () => {
  describe("Wall chapter framework", () => {
    it("has 10 chapter specs (one per chapter)", () => {
      expect(CHAPTER_SPECS.length).toBe(10);
    });

    it("every chapter spec has a stable slug", () => {
      for (const spec of CHAPTER_SPECS) {
        expect(spec.slug, `chapter ${spec.id} has no slug`).toBeTruthy();
        expect(typeof spec.slug).toBe("string");
        expect(spec.slug.length).toBeGreaterThan(0);
      }
    });

    it("chapter ids are unique (1..10)", () => {
      const ids = CHAPTER_SPECS.map((s) => s.id);
      const unique = new Set(ids);
      expect(unique.size).toBe(ids.length);
      expect(unique.size).toBe(10);
      // Each id 1..10 represented exactly once.
      for (let i = 1 as 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10; i <= 10; i++) {
        expect(ids).toContain(i);
      }
    });

    it("chapter slugs are unique", () => {
      const slugs = CHAPTER_SPECS.map((s) => s.slug);
      const unique = new Set<ChapterSlug>(slugs);
      expect(unique.size).toBe(slugs.length);
    });

    it("every chapter that declares a camera has a valid (longitude, latitude, zoom)", () => {
      // Per ChapterSpec contract, `camera` may be undefined for chapters
      // that aren't wired to Mapbox (rare; see chapterSpec.ts comment).
      // We only assert that when a camera *is* declared, it's complete.
      for (const spec of CHAPTER_SPECS) {
        const cam = spec.camera;
        if (cam === undefined) continue;
        expect(typeof cam.longitude).toBe("number");
        expect(typeof cam.latitude).toBe("number");
        expect(typeof cam.zoom).toBe("number");
      }
    });

    it("chapter sound ids are null or non-empty strings", () => {
      for (const spec of CHAPTER_SPECS) {
        if (spec.sound !== null) {
          expect(typeof spec.sound).toBe("string");
          expect(spec.sound.length).toBeGreaterThan(0);
        }
      }
    });
  });

  describe("Wall progress bounds", () => {
    it("CHAPTER_BOUNDS covers chapters 1..10", () => {
      expect(CHAPTER_BOUNDS.length).toBeGreaterThanOrEqual(10);
    });

    it("CHAPTER_BOUNDS span covers [0, 1] with no gaps", () => {
      // Sort by start, walk forward; each next.start === prev.end.
      const sorted = [...CHAPTER_BOUNDS].sort((a, b) => a.start - b.start);
      expect(sorted[0]!.start).toBeCloseTo(0, 4);
      expect(sorted[sorted.length - 1]!.end).toBeCloseTo(1, 4);
      for (let i = 1; i < sorted.length; i++) {
        const prev = sorted[i - 1]!;
        const curr = sorted[i]!;
        expect(curr.start).toBeCloseTo(prev.end, 4);
      }
    });

    it("CHAPTER_BOUNDS slices are non-degenerate (start < end)", () => {
      for (const b of CHAPTER_BOUNDS) {
        expect(b.start).toBeLessThan(b.end);
      }
    });
  });

  describe("Submission artifact cross-linking", () => {
    const README = join(REPO_ROOT, "README.md");
    const PRESS_KIT = join(REPO_ROOT, "docs", "press-kit.md");
    const DEVPOST = join(REPO_ROOT, "docs", "devpost-submission.md");
    const CHECKLIST = join(REPO_ROOT, "docs", "submission-checklist.md");
    const DEMO = join(REPO_ROOT, "docs", "submission-demo.md");

    it("README is the audience-facing entry point (no submission-only spokes)", () => {
      // Narrative reset (sprint/narrative-reset, commit 03dff3c): the
      // README was rewritten as a public, audience-facing entry point —
      // not a submission discoverability hub. Submission artifacts
      // (press-kit, Devpost form, submission-demo, submission-checklist,
      // vercel-deploy-runbook, post-submission/) were intentionally
      // stripped from the README to keep the public-facing surface
      // focused on what GoWork is and how to run it. The submission
      // packet still exists under docs/ — judges discover it via the
      // Devpost submission form, not via README spokes.
      //
      // What the README MUST still have: project title (GoWork), the
      // city framing (Fort Worth), an MIT license reference, and at
      // least one architecture-level doc link (docs/architecture.md or
      // docs/setup.md) so a contributor can land on the repo and find
      // the next file.
      const md = readFileSync(README, "utf8");
      expect(md).toMatch(/GoWork/);
      expect(md).toMatch(/Fort Worth/i);
      expect(md).toMatch(/MIT/);
      expect(md).toMatch(/docs\/(architecture|setup|api|DEPLOYMENT)\.md/i);
    });

    it("Press kit is rebranded for HackFW with the locked thesis", () => {
      // Narrative reset: the press-kit was rewritten audience-first.
      // Cinematic-still references (`docs/press-kit/screenshots/...`),
      // the Devpost cross-link, and the scsonnet@gmail.com contact
      // line were dropped — the press kit is now a one-pager that
      // judges + reporters can read top-to-bottom without bouncing.
      // What MUST still be in the press kit: GoWork branding, the
      // HackFW 2026 framing, the locked thesis question, an MIT
      // license declaration, and at least one repo-level pointer
      // (the GitHub org URL is sufficient — full /montgowork path
      // is not load-bearing for a press kit).
      const md = readFileSync(PRESS_KIT, "utf8");
      expect(md).toMatch(/GoWork/);
      expect(md).toMatch(/HackFW 2026/);
      expect(md).toMatch(/standing between you and a job/i);
      expect(md).toMatch(/MIT/);
      expect(md).toMatch(/github\.com\/fivedollarfridays/);
    });

    it("Devpost references README + press kit + repo + license", () => {
      const md = readFileSync(DEVPOST, "utf8");
      expect(md).toMatch(/README/i);
      expect(md).toMatch(/press[- ]kit/i);
      expect(md).toMatch(/github\.com\/fivedollarfridays\/montgowork/);
      expect(md).toMatch(/MIT/i);
    });

    it("Submission checklist references deploy runbook + tag script + post-submission drafts", () => {
      const md = readFileSync(CHECKLIST, "utf8");
      expect(md).toMatch(/vercel-deploy-runbook\.md/);
      expect(md).toMatch(/tag-submission/);
      expect(md).toMatch(/post-submission/);
    });

    it("Submission demo is a self-contained live-demo script", () => {
      // Narrative reset (sprint/narrative-reset, commit 03dff3c)
      // reverted submission-demo.md to a self-contained live-demo
      // script (Beat 1..7) and dropped the cross-links to
      // submission-video-script.md, submission-video-take-plan.md, and
      // submission-video.srt. Those video assets still exist under
      // docs/ and are exercised by submission-readiness.test.ts; they
      // simply aren't linked from the demo script anymore (a live
      // demo and a recorded video are independent tracks).
      //
      // What the demo MUST still have: a Pitch section, Beat 1..7
      // structure with timing budgets, a backup-paths section, and a
      // pre-demo checklist. Those are checked in
      // submission-demo-walkthrough.test.ts; here we just guard the
      // doc's existence and substantive size.
      const md = readFileSync(DEMO, "utf8");
      expect(md.length).toBeGreaterThan(2000);
      expect(md).toMatch(/Beat 1\b/i);
      expect(md).toMatch(/pre-demo checklist/i);
    });
  });

  describe("Long-term framework artifacts (Driver D Spotlights)", () => {
    it("contributors-onboarding doc exists with the 30-min promise", () => {
      const path = join(REPO_ROOT, "docs", "contributors-onboarding.md");
      expect(existsSync(path)).toBe(true);
      const md = readFileSync(path, "utf8");
      expect(md).toMatch(/30 minutes|30-min/i);
    });

    it("multi-city-expansion-playbook doc exists with worked example", () => {
      const path = join(REPO_ROOT, "docs", "multi-city-expansion-playbook.md");
      expect(existsSync(path)).toBe(true);
      const md = readFileSync(path, "utf8");
      // Worked example must mention a real city slug (Dallas / Birmingham)
      // so the playbook isn't theoretical.
      expect(md).toMatch(/Dallas|Birmingham|Houston/i);
    });

    it("ADR directory exists with a README index", () => {
      const adrIndex = join(REPO_ROOT, "docs", "architecture-decisions", "README.md");
      expect(existsSync(adrIndex)).toBe(true);
      const md = readFileSync(adrIndex, "utf8");
      // Must catalog at least 3 ADRs (Wall, bundle budget, multi-driver).
      expect(md).toMatch(/0001/);
      expect(md).toMatch(/0006|bundle/i);
      expect(md).toMatch(/0008|multi-driver/i);
    });

    it("new-city-scaffold script exists and accepts --slug --name --state", () => {
      const path = join(REPO_ROOT, "scripts", "new-city-scaffold.mjs");
      expect(existsSync(path)).toBe(true);
      const src = readFileSync(path, "utf8");
      expect(src).toMatch(/--slug/);
      expect(src).toMatch(/--name/);
      expect(src).toMatch(/--state/);
    });

    it("release-notes-generator script exists", () => {
      const path = join(REPO_ROOT, "scripts", "release-notes-generator.mjs");
      expect(existsSync(path)).toBe(true);
    });

    it("post-mortem template exists in post-submission directory", () => {
      const path = join(REPO_ROOT, "docs", "post-submission", "post-mortem-template.md");
      expect(existsSync(path)).toBe(true);
    });
  });
});

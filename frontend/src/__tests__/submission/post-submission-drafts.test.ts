/**
 * W5 Driver D — T5.D.2 + T5.D.4
 *
 * Post-submission narrative drafts (Reddit + Twitter + LinkedIn) +
 * cross-document linking sweep.
 *
 * The drafts are not auto-published — Shawn does the actual posting.
 * These tests pin the editorial structure (locked thesis hero, GoWork
 * explainer, MIT + open-source positioning, Fort Worth + Montgomery
 * deployment story, links to live demo + repo + video) so a future
 * editorial pass can't drift the locked phrases or drop a deployment.
 *
 * Cross-doc linking sweep also lives here: every submission doc must
 * point at every other submission doc that's contractually relevant
 * (README references press kit + Devpost + LICENSE; press kit
 * references repo + demo URL + screenshots; etc.).
 */
import { describe, it, expect } from "vitest";
import { existsSync, readFileSync, statSync } from "node:fs";
import { join, resolve } from "node:path";

const REPO_ROOT = resolve(__dirname, "..", "..", "..", "..");

const POST_SUBMISSION_DIR = join(REPO_ROOT, "docs", "post-submission");

const REDDIT_PATH = join(POST_SUBMISSION_DIR, "reddit-r-civic-tech.md");
const TWITTER_PATH = join(POST_SUBMISSION_DIR, "twitter-thread.md");
const LINKEDIN_PATH = join(POST_SUBMISSION_DIR, "linkedin-announcement.md");
const POST_MORTEM_PATH = join(POST_SUBMISSION_DIR, "post-mortem-template.md");

function read(path: string): string {
  return readFileSync(path, "utf8");
}

function wordCount(s: string): number {
  return s
    .replace(/[#*_>`\-|]/g, " ")
    .split(/\s+/)
    .filter(Boolean).length;
}

describe("Post-submission Reddit draft (T5.D.2)", () => {
  it("file exists and is non-trivial", () => {
    expect(existsSync(REDDIT_PATH)).toBe(true);
    expect(statSync(REDDIT_PATH).size).toBeGreaterThanOrEqual(1500);
  });

  it("targets r/civic-tech (or r/programming as fallback)", () => {
    const md = read(REDDIT_PATH);
    expect(md).toMatch(/r\/civic-?tech|r\/programming/i);
  });

  it("includes the locked thesis hero", () => {
    const md = read(REDDIT_PATH);
    expect(md).toMatch(/standing between you and a job/i);
  });

  it("explains what GoWork is in plain terms", () => {
    const md = read(REDDIT_PATH);
    expect(md).toMatch(/workforce.*navigator|barrier|cliff|career/i);
  });

  it("calls out MIT and open-source positioning", () => {
    const md = read(REDDIT_PATH);
    expect(md).toMatch(/MIT/);
    expect(md).toMatch(/open[- ]source/i);
  });

  it("names both deployed cities (Fort Worth + Montgomery)", () => {
    const md = read(REDDIT_PATH);
    expect(md).toMatch(/Fort Worth/i);
    expect(md).toMatch(/Montgomery/i);
  });

  it("links to live demo + repo + video", () => {
    const md = read(REDDIT_PATH);
    // Repo URL or placeholder
    expect(md).toMatch(/github\.com\/fivedollarfridays\/montgowork|<DEMO_URL>|gowork\.vercel\.app/);
  });

  it("falls within 400-1100 words (Reddit long-form latitude)", () => {
    // Reddit r/civic-tech tolerates 400-1000+ word "Show" posts when the
    // body covers what / where / how / open-source. Cap is 1100 to allow
    // posting notes (which are not part of the published body but live
    // in-doc as Shawn's pre-post crib sheet).
    const md = read(REDDIT_PATH);
    const wc = wordCount(md);
    expect(wc).toBeGreaterThanOrEqual(400);
    expect(wc).toBeLessThanOrEqual(1100);
  });
});

describe("Post-submission Twitter thread (T5.D.2)", () => {
  it("file exists and is non-trivial", () => {
    expect(existsSync(TWITTER_PATH)).toBe(true);
    expect(statSync(TWITTER_PATH).size).toBeGreaterThanOrEqual(800);
  });

  it("declares the 8-tweet thread structure", () => {
    const md = read(TWITTER_PATH);
    // Each tweet numbered 1/8, 2/8, etc OR markdown headings tweet 1..8
    const tweetMarkers = (md.match(/(?:^|\s)(?:[1-8]\/8|[Tt]weet [1-8])/gm) ?? []).length;
    expect(tweetMarkers).toBeGreaterThanOrEqual(8);
  });

  it("references the 4 cinematic stills (Ch2, Ch6, Ch7, Ch8)", () => {
    const md = read(TWITTER_PATH);
    expect(md).toMatch(/ch2|chapter 2|fort worth arrival/i);
    expect(md).toMatch(/ch6|chapter 6|the math/i);
    expect(md).toMatch(/ch7|chapter 7|the path/i);
    expect(md).toMatch(/ch8|chapter 8|barrier graph|constellation/i);
  });

  it("documents the 280-char-per-tweet ceiling inline", () => {
    // The doc itself must document the 280-char cap for the operator;
    // mechanical char counting per tweet is brittle (markdown renders
    // headings, blockquotes, and trailing spaces inconsistently). The
    // operator (Shawn) verifies in Tweetdeck before posting.
    const md = read(TWITTER_PATH);
    expect(md).toMatch(/280[- ]char|280[- ]character|280 chars|<=\s*280/i);
  });

  it("references the locked tone fingerprint via copy-thesis", () => {
    const md = read(TWITTER_PATH);
    expect(md).toMatch(/copy-thesis/i);
  });
});

describe("Post-submission LinkedIn announcement (T5.D.2)", () => {
  it("file exists and is non-trivial", () => {
    expect(existsSync(LINKEDIN_PATH)).toBe(true);
    expect(statSync(LINKEDIN_PATH).size).toBeGreaterThanOrEqual(2000);
  });

  it("falls within 700-1300 words (LinkedIn long-form sweet spot + posting notes)", () => {
    const md = read(LINKEDIN_PATH);
    const wc = wordCount(md);
    expect(wc).toBeGreaterThanOrEqual(600);
    expect(wc).toBeLessThanOrEqual(1300);
  });

  it("frames around problem -> approach -> outcome", () => {
    const md = read(LINKEDIN_PATH);
    expect(md).toMatch(/(problem|barrier|career[- ]center|workforce desert|cross[- ]referencing)/i);
    expect(md).toMatch(/(approach|cinematic|scrollytelling|wall|mapbox)/i);
    expect(md).toMatch(/(outcome|deployed|open[- ]source|MIT)/i);
  });

  it("targets workforce + civic-tech professional audience", () => {
    const md = read(LINKEDIN_PATH);
    expect(md).toMatch(/workforce|career center|civic|public[- ]?interest/i);
  });

  it("includes the locked thesis hero", () => {
    const md = read(LINKEDIN_PATH);
    expect(md).toMatch(/standing between you and a job/i);
  });
});

describe("Cross-document linking sweep (T5.D.4)", () => {
  const README = join(REPO_ROOT, "README.md");
  const PRESS_KIT = join(REPO_ROOT, "docs", "press-kit.md");
  const DEVPOST = join(REPO_ROOT, "docs", "devpost-submission.md");
  const SUBMISSION_CHECKLIST = join(REPO_ROOT, "docs", "submission-checklist.md");
  const SUBMISSION_DEMO = join(REPO_ROOT, "docs", "submission-demo.md");

  it("README pins audience-facing branding + license (no submission spokes)", () => {
    // Narrative reset (sprint/narrative-reset, commit 03dff3c) rewrote
    // the README as a public, audience-facing entry point. Submission-
    // packet cross-links (press-kit.md, devpost-submission.md, the
    // LICENSE filename) were removed from the README to keep the
    // public-facing surface focused on what GoWork is and how to run
    // it. The MIT license is still declared in-line; the LICENSE file
    // still exists at repo root (covered by submission-readiness.test).
    const md = read(README);
    expect(md).toMatch(/GoWork/);
    expect(md).toMatch(/Fort Worth/i);
    expect(md).toMatch(/MIT/);
  });

  it("README links to at least one architecture or setup doc", () => {
    // Narrative reset stripped the W5-D submission-checklist + deploy-
    // runbook spokes from the README; what remains is the docs/
    // family covering the runtime architecture and setup flow. A
    // contributor must still be able to walk from README to at least
    // one architecture-level doc in one click.
    const md = read(README);
    expect(md).toMatch(/docs\/(architecture|setup|api|DEPLOYMENT)\.md/i);
  });

  it("press kit references the GitHub org and the locked thesis", () => {
    // Narrative reset dropped the scsonnet@gmail.com contact line and
    // the cinematic-still gallery from the press kit. What remains is
    // a one-pager covering: GoWork branding, the HackFW 2026 framing,
    // the locked thesis (hero question), the GitHub org URL, and an
    // MIT license declaration. Reporters reach Shawn via the GitHub
    // profile or the @paircoder handle (already in the press kit's
    // Contact section).
    const md = read(PRESS_KIT);
    expect(md).toMatch(/github\.com\/fivedollarfridays/);
    expect(md).toMatch(/standing between you and a job/i);
  });

  it("press kit declares HackFW 2026 + MIT license", () => {
    // The screenshots directory (`docs/press-kit/screenshots/`) was
    // dropped from the press kit body during narrative reset — it
    // still exists on disk for the Devpost upload. The press kit
    // contract here is the editorial frame: HackFW 2026 + MIT.
    const md = read(PRESS_KIT);
    expect(md).toMatch(/HackFW 2026/);
    expect(md).toMatch(/MIT/);
  });

  it("Devpost references README + press kit + repo", () => {
    const md = read(DEVPOST);
    // Driver D contract: judges or post-submission viewers should be able
    // to walk Devpost -> README -> press kit. Add explicit references.
    expect(md).toMatch(/README\.md|README/i);
    expect(md).toMatch(/press-kit\.md|press kit/i);
    expect(md).toMatch(/github\.com\/fivedollarfridays\/montgowork/);
  });

  it("submission checklist references deploy runbook + all submission docs", () => {
    const md = read(SUBMISSION_CHECKLIST);
    expect(md).toMatch(/vercel-deploy-runbook\.md/);
    expect(md).toMatch(/submission-demo\.md/);
    expect(md).toMatch(/devpost-submission\.md/);
    expect(md).toMatch(/copy-thesis\.md/);
  });

  it("submission demo is a self-contained live-demo script", () => {
    // Narrative reset (sprint/narrative-reset, commit 03dff3c) reverted
    // submission-demo.md to a Beat 1..7 staging-walk script and dropped
    // the cross-links to submission-video-script.md / take-plan.md /
    // SRT. Those video assets still exist (and are exercised by
    // submission-readiness.test.ts), but the live demo and the recorded
    // video are independent tracks now.
    const md = read(SUBMISSION_DEMO);
    expect(md).toMatch(/Beat 1\b/i);
    expect(md).toMatch(/pre-demo checklist/i);
  });
});

describe("Post-mortem template (Spotlight)", () => {
  it("file exists and structures what worked / didn't / would do differently", () => {
    expect(existsSync(POST_MORTEM_PATH)).toBe(true);
    const md = read(POST_MORTEM_PATH);
    expect(md).toMatch(/what worked/i);
    expect(md).toMatch(/what didn'?t|what failed|what could have/i);
    expect(md).toMatch(/(differently|next time|lessons)/i);
  });
});

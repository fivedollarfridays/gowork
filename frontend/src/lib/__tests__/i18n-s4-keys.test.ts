import { describe, it, expect, beforeEach } from "vitest";
import { getTranslation, setLocale } from "../i18n";

/**
 * Verify all S4 component translation keys exist in both EN and ES.
 * These keys cover: BarrierSequenceViz, WhatHappensIf, SharePlanButton,
 * VoiceInput, CaseManager dashboard, OutcomesBadge.
 */
describe("i18n S4 component keys", () => {
  beforeEach(() => {
    setLocale("en");
  });

  const S4_KEYS = [
    // Share
    "share.shareButton",
    "share.sharing",
    "share.shareFailed",
    // Sequence
    "sequence.heading",
    "sequence.description",
    "sequence.noBarriers",
    "sequence.estimatedTotal",
    "sequence.weeks",
    "sequence.unlocks",
    "sequence.cycleWarning",
    // Simulator
    "simulator.heading",
    "simulator.description",
    "simulator.noBarriers",
    "simulator.reset",
    "simulator.calculating",
    "simulator.jobsAccessible",
    "simulator.benefitsUnlocked",
    "simulator.cascadingUnlocks",
    "simulator.summarySentence",
    // Voice
    "voice.startVoice",
    "voice.stopVoice",
    "voice.listening",
    "voice.unsupported",
    // Dashboard
    "dashboard.heading",
    "dashboard.description",
    "dashboard.totalAssessments",
    "dashboard.barrierInstances",
    "dashboard.avgBarriers",
    "dashboard.commonBarriers",
    "dashboard.loadingStats",
    "dashboard.loadFailed",
    // Outcomes
    "outcomes.assessmentsCompleted",
    "outcomes.improvingRecommendations",
  ];

  describe("English translations", () => {
    for (const key of S4_KEYS) {
      it(`has EN translation for ${key}`, () => {
        const result = getTranslation(key, "en");
        expect(result).not.toBe(key);
        expect(result.length).toBeGreaterThan(0);
      });
    }
  });

  describe("Spanish translations", () => {
    for (const key of S4_KEYS) {
      it(`has ES translation for ${key}`, () => {
        const result = getTranslation(key, "es");
        expect(result).not.toBe(key);
        expect(result.length).toBeGreaterThan(0);
      });
    }
  });

  describe("Spanish is distinct from English", () => {
    const DISTINCT_KEYS = [
      "sequence.heading",
      "simulator.heading",
      "dashboard.heading",
      "voice.listening",
    ];

    for (const key of DISTINCT_KEYS) {
      it(`ES translation for ${key} differs from EN`, () => {
        const en = getTranslation(key, "en");
        const es = getTranslation(key, "es");
        expect(en).not.toBe(es);
      });
    }
  });
});

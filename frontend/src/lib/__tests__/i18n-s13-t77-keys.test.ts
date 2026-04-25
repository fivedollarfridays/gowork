import { describe, it, expect, beforeEach } from "vitest";
import { getTranslation, setLocale, t } from "../i18n";

/**
 * Regression test for T13.77 — homepage / credit / plan empty-state /
 * case-manager / assess step-chrome keys must exist in both locales and
 * the ES values must differ from EN (no untranslated passthrough).
 *
 * The static `test_i18n_completeness.py` gate covers structural parity;
 * this file pins the *specific* keys this sprint adds so a regression
 * (e.g. someone deleting `home.heroQuestion` from one locale) shows up
 * as a focused test failure, not just a generic key-set diff.
 */

const KEYS_THIS_SPRINT_ADDS = [
  // Home (F-1)
  "home.heroQuestion",
  "home.heroBlurb",
  "home.ctaPlan",
  "home.ctaCredit",
  "home.howHeading",
  "home.stepLabel",
  "home.stepAssessTitle",
  "home.stepAssessDesc",
  "home.stepMatchTitle",
  "home.stepMatchDesc",
  "home.stepPlanTitle",
  "home.stepPlanDesc",
  "home.numbersHeading",
  "home.numbersSubtitlePrefix",
  "home.statPoverty",
  "home.statLabor",
  "home.bottomCtaTitle",
  "home.bottomCtaBody",
  "home.bottomCtaButton",
  // Credit (F-2)
  "credit.heading",
  "credit.scoreLabel",
  "credit.utilizationLabel",
  "credit.paymentHistoryLabel",
  "credit.accountAgeLabel",
  "credit.totalAccountsLabel",
  "credit.openAccountsLabel",
  "credit.assessButton",
  "credit.analyzing",
  "credit.tryAgain",
  "credit.barrierSeverityLabel",
  "credit.encouragement",
  "credit.thresholdsHeading",
  "credit.thresholdMet",
  "credit.thresholdDays",
  "credit.eligibilityHeading",
  "credit.runAnother",
  // Plan empty-state (F-4)
  "plan.emptyNoSession",
  "plan.emptyNoToken",
  "plan.emptyStartCta",
  "plan.errorNotFound",
  "plan.errorGeneric",
  "plan.errorFallback",
  "plan.errorStartNew",
  "plan.matchesEmptyTitle",
  "plan.matchesEmptyDesc",
  "plan.matchesEmptyAction",
  "plan.yourBarriers",
  "plan.creditAssessmentHeading",
  "plan.jobReadinessHeading",
  "plan.whatsNextHeading",
  "plan.whatsNextDownloadStrong",
  "plan.whatsNextDownloadDesc",
  "plan.whatsNextBringPlanPrefix",
  "plan.whatsNextAskCaseManager",
  "plan.whatsNextAskCaseManagerDesc",
  "plan.whatsNextStartNew",
  // Assess step chrome (F-5)
  "assess.stepBasicInfo",
  "assess.stepResume",
  "assess.stepBarriers",
  "assess.stepRecord",
  "assess.stepBenefits",
  "assess.stepSchedule",
  "assess.stepIndustries",
  "assess.stepCredit",
  "assess.stepReview",
  "assess.errorSubmit",
  "assess.errorCredit",
];

describe("T13.77 ES-locale translation pass — key coverage", () => {
  beforeEach(() => {
    setLocale("en");
  });

  it("every new key resolves to a non-empty EN string", () => {
    const missing = KEYS_THIS_SPRINT_ADDS.filter((key) => {
      const value = getTranslation(key, "en");
      return value === key || value.trim() === "";
    });
    expect(missing).toEqual([]);
  });

  it("every new key resolves to a non-empty ES string", () => {
    const missing = KEYS_THIS_SPRINT_ADDS.filter((key) => {
      const value = getTranslation(key, "es");
      return value === key || value.trim() === "";
    });
    expect(missing).toEqual([]);
  });

  it("ES values differ from EN values (translation actually happened)", () => {
    // Allow a known short identical pair: 'Error:' → 'Error:' (Latinism,
    // covered in IDENTICAL_PAIR_ALLOWLIST in test_i18n_completeness.py).
    const allowedIdentical = new Set(["credit.errorPrefix"]);
    const untranslated = KEYS_THIS_SPRINT_ADDS.filter((key) => {
      if (allowedIdentical.has(key)) return false;
      return getTranslation(key, "en") === getTranslation(key, "es");
    });
    expect(untranslated).toEqual([]);
  });

  it("setLocale('es') flips t() output for a representative new key", () => {
    setLocale("en");
    const enValue = t("home.heroQuestion");
    setLocale("es");
    const esValue = t("home.heroQuestion");
    expect(enValue).not.toBe(esValue);
    expect(esValue).toContain("¿");
  });

  it("ES homepage CTA uses informal `tu` register, not machine-translated", () => {
    // Anchors the tone choice — if someone replaces this with a literal
    // "Conseguir Su Plan" (formal usted) machine translation, this fires.
    const ctaPlan = getTranslation("home.ctaPlan", "es");
    expect(ctaPlan.toLowerCase()).toContain("tu");
  });

  it("the four T13.77 ES accent fixes are in place", () => {
    expect(getTranslation("assess.basicInfoTitle", "es")).toBe(
      "Cuéntanos sobre ti",
    );
    expect(getTranslation("assess.navDesc", "es")).toContain("reinserción");
    expect(getTranslation("assess.iHaveVehicle", "es")).toBe("Tengo vehículo");
    expect(getTranslation("assess.scheduleDesc", "es")).toContain("Indícanos");
  });
});

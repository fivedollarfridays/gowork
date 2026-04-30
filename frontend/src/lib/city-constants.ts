/**
 * City-specific constants and helpers.
 *
 * GoWork's reference deployment is Fort Worth, TX. The Alabama /
 * Montgomery codepaths are LEGACY (the original Alabama demo)
 * and are only reachable when a caller explicitly passes
 * `state === "AL"`. All defaults flipped to Texas so any subpage
 * that doesn't thread the state prop still renders Fort Worth
 * copy + Fort Worth ZIP validation + Texas service URLs.
 */

export const MONTGOMERY_ZIP_REGEX = /^361\d{2}$/;
export const FORT_WORTH_ZIP_REGEX = /^761\d{2}$/;

/** City-aware ZIP validation. Defaults to Fort Worth (Texas).
 *  Pass `state="AL"` for legacy Montgomery validation. */
export function isValidCityZip(zip: string, state?: string): boolean {
  if (state === "AL") return MONTGOMERY_ZIP_REGEX.test(zip);
  return FORT_WORTH_ZIP_REGEX.test(zip);
}

export const CAREER_CENTER_AL = {
  name: "Montgomery Career Center",
  address: "1060 East South Boulevard, Montgomery, AL 36116",
  phone: "334-286-1746",
  hours: "Monday \u2013 Friday, 8:00 AM \u2013 5:00 PM",
} as const;

export const CAREER_CENTER_TX = {
  name: "Workforce Solutions for Tarrant County",
  address: "1200 Circle Dr, Fort Worth, TX 76119",
  phone: "817-413-4400",
  hours: "Monday \u2013 Friday, 8:00 AM \u2013 5:00 PM",
} as const;

/** Get career center for active city. Defaults to Fort Worth (TX). */
export function getCareerCenter(state?: string) {
  return state === "AL" ? CAREER_CENTER_AL : CAREER_CENTER_TX;
}

export const PROGRAM_LABELS_AL: Record<string, string> = {
  SNAP: "SNAP",
  TANF: "TANF",
  Medicaid: "Medicaid",
  ALL_Kids: "ALL Kids",
  Childcare_Subsidy: "Childcare",
  Section_8: "Section 8",
  LIHEAP: "LIHEAP",
};

export const PROGRAM_LABELS_TX: Record<string, string> = {
  SNAP: "SNAP",
  TANF: "TANF",
  Medicaid: "Medicaid",
  CHIP: "CHIP",
  Childcare_Subsidy: "Childcare",
  Section_8: "Section 8",
  CEAP: "CEAP",
};

/** Get program labels for active city. Defaults to Texas. */
export function getProgramLabels(state?: string): Record<string, string> {
  return state === "AL" ? PROGRAM_LABELS_AL : PROGRAM_LABELS_TX;
}

/** City display label (e.g. "Fort Worth, TX" or legacy "Montgomery, AL"). */
export function getCityLabel(state?: string): string {
  return state === "AL" ? "Montgomery, AL" : "Fort Worth, TX";
}

/** Area description for the assess page intro text. */
export function getCityAreaDescription(state?: string): string {
  return state === "AL"
    ? "We serve the Montgomery, Alabama area. Enter your ZIP code to get started."
    : "We serve the Fort Worth, Texas area. Enter your ZIP code to get started.";
}

/** Example ZIP placeholder for the input field. */
export function getZipPlaceholder(state?: string): string {
  return state === "AL" ? "36104" : "76102";
}

/** Error message when ZIP is invalid for the active city. */
export function getZipErrorMessage(state?: string): string {
  return state === "AL"
    ? "Please enter a Montgomery area ZIP (361xx)"
    : "Please enter a Fort Worth area ZIP (761xx)";
}

/** State job board URL. */
export function getJobBoardUrl(state?: string): string {
  return state === "AL"
    ? "https://joblink.alabama.gov/"
    : "https://www.workintexas.com/";
}

/** Legal services URL for the active state. */
export function getLegalServicesUrl(state?: string): string {
  return state === "AL"
    ? "https://www.legalservicesalabama.org/"
    : "https://www.lanwt.org/";
}

/** Housing authority URL for the active city. */
export function getHousingUrl(state?: string): string {
  return state === "AL"
    ? "https://www.hamd.org/"
    : "https://www.fwhs.org/";
}

/** Childcare assistance URL for the active state. */
export function getChildcareUrl(state?: string): string {
  return state === "AL"
    ? "https://dhr.alabama.gov/child-care/"
    : "https://www.twc.texas.gov/programs/child-care-services";
}

/** Fallback benefits portal URL for the active state. */
export function getBenefitsFallbackUrl(state?: string): string {
  return state === "AL"
    ? "https://www.alabamabenefits.gov/"
    : "https://www.yourtexasbenefits.com/";
}

/**
 * City-specific constants and helpers.
 *
 * Extracted from constants.ts to stay under the 15-function-per-file
 * architecture limit. All functions accept an optional `state` param
 * and default to Alabama (Montgomery) for backward compatibility.
 */

export const MONTGOMERY_ZIP_REGEX = /^361\d{2}$/;
export const FORT_WORTH_ZIP_REGEX = /^761\d{2}$/;

/** City-aware ZIP validation. Defaults to Montgomery for backward compatibility. */
export function isValidCityZip(zip: string, state?: string): boolean {
  if (state === "TX") return FORT_WORTH_ZIP_REGEX.test(zip);
  return MONTGOMERY_ZIP_REGEX.test(zip);
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

/** Get career center for active city. Defaults to Montgomery. */
export function getCareerCenter(state?: string) {
  return state === "TX" ? CAREER_CENTER_TX : CAREER_CENTER_AL;
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

/** Get program labels for active city. Defaults to Alabama. */
export function getProgramLabels(state?: string): Record<string, string> {
  return state === "TX" ? PROGRAM_LABELS_TX : PROGRAM_LABELS_AL;
}

/** City display label (e.g. "Montgomery, AL" or "Fort Worth, TX"). */
export function getCityLabel(state?: string): string {
  return state === "TX" ? "Fort Worth, TX" : "Montgomery, AL";
}

/** Area description for the assess page intro text. */
export function getCityAreaDescription(state?: string): string {
  return state === "TX"
    ? "We serve the Fort Worth, Texas area. Enter your ZIP code to get started."
    : "We serve the Montgomery, Alabama area. Enter your ZIP code to get started.";
}

/** Example ZIP placeholder for the input field. */
export function getZipPlaceholder(state?: string): string {
  return state === "TX" ? "76102" : "36104";
}

/** Error message when ZIP is invalid for the active city. */
export function getZipErrorMessage(state?: string): string {
  return state === "TX"
    ? "Please enter a Fort Worth area ZIP (761xx)"
    : "Please enter a Montgomery area ZIP (361xx)";
}

/** State job board URL. */
export function getJobBoardUrl(state?: string): string {
  return state === "TX"
    ? "https://www.workintexas.com/"
    : "https://joblink.alabama.gov/";
}

/** Legal services URL for the active state. */
export function getLegalServicesUrl(state?: string): string {
  return state === "TX"
    ? "https://www.lanwt.org/"
    : "https://www.legalservicesalabama.org/";
}

/** Housing authority URL for the active city. */
export function getHousingUrl(state?: string): string {
  return state === "TX"
    ? "https://www.fwhs.org/"
    : "https://www.hamd.org/";
}

/** Childcare assistance URL for the active state. */
export function getChildcareUrl(state?: string): string {
  return state === "TX"
    ? "https://www.twc.texas.gov/programs/child-care-services"
    : "https://dhr.alabama.gov/child-care/";
}

/** Fallback benefits portal URL for the active state. */
export function getBenefitsFallbackUrl(state?: string): string {
  return state === "TX"
    ? "https://www.yourtexasbenefits.com/"
    : "https://www.alabamabenefits.gov/";
}

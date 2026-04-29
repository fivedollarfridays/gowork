/**
 * Driver C — sprint/gowork-facelift Ch6 LiveJobs employer registry.
 *
 * Single source of truth for the three hero job cards on the homepage
 * Ch6 LiveJobs section. Sibling to `lib/wall/employerRegistry.ts`
 * (DFW5 etc.) but scoped to the marketing landing — these three are
 * Carlos's *Tuesday narrative* destinations: Alcon, BNSF, JE Dunn.
 *
 * Used by:
 *   - `Chapter04TheMap` — paths source + markers (alcon, bnsf, dunn)
 *   - `Chapter06LiveJobs` — JobCard renderer + `/assess?employer={id}`
 *   - any future ts-only consumer (analytics, OG cards, etc.)
 *
 * Display copy (name / blurb) is intentionally English-canonical here;
 * Spanish equivalents live in the i18n bundle under `home.ch6.cards.*`.
 */

export interface HomeEmployer {
  /** Stable id used for URL params + map sources/layers. */
  id: "alcon" | "bnsf" | "dunn";
  /** Two-letter logo glyph rendered in the JobCard square chip. */
  logo: string;
  /** Color hint for the logo chip background — matches the mock. */
  logoColor: "amber" | "cyan" | "green";
  /** Public-facing employer name (EN canonical). */
  name: string;
  /** Single-line street address. */
  address: string;
  /** Display wage including unit, e.g. "$22.50/hr". */
  wage: string;
  /** Commute summary line, e.g. "42m · Route 7". */
  commute: string;
  /** Shift summary, e.g. "3:30p–11:30p · M-F". */
  shift: string;
  /** Card body blurb (EN canonical). */
  blurb: string;
  /** Longitude (Fort Worth bbox). */
  longitude: number;
  /** Latitude (Fort Worth bbox). */
  latitude: number;
}

export const HOME_EMPLOYER_IDS = ["alcon", "bnsf", "dunn"] as const;

export const HOME_EMPLOYERS: readonly HomeEmployer[] = [
  {
    id: "alcon",
    logo: "AL",
    logoColor: "amber",
    name: "Alcon — Production Tech II",
    address: "Alcon Drive · Fort Worth · 76134",
    wage: "$22.50/hr",
    commute: "42m · Route 7",
    shift: "3:30p–11:30p · M-F",
    blurb:
      "Hires through navigator referral. Background reviewed individually — no auto-disqualify. Pre-apprenticeship pays through training.",
    longitude: -97.27,
    latitude: 32.834,
  },
  {
    id: "bnsf",
    logo: "BN",
    logoColor: "cyan",
    name: "BNSF — CDL Driver Trainee",
    address: "Lancaster Ave · Fort Worth · 76104",
    wage: "$26.10/hr",
    commute: "18m · Route 2",
    shift: "4-on / 3-off",
    blurb:
      "License unblocks this in 90 minutes at DPS. Trainee program pays from day one. Background reviewed by panel — felonies older than five years frequently approved.",
    longitude: -97.329,
    latitude: 32.751,
  },
  {
    id: "dunn",
    logo: "JC",
    logoColor: "green",
    name: "JE Dunn — Apprentice Electrician",
    address: "I-35W Corridor · Fort Worth · 76106",
    wage: "$19.75/hr",
    commute: "36m · I-35W",
    shift: "4-yr paid · journeyman in 4y",
    blurb:
      "Pre-apprenticeship is paid. Tools provided. Scales to $38/hr at journeyman. JE Dunn partners with Tarrant fair-chance navigators directly.",
    longitude: -97.347,
    latitude: 32.705,
  },
] as const;

const BY_ID = new Map<string, HomeEmployer>();
for (const e of HOME_EMPLOYERS) BY_ID.set(e.id, e);

/** Lookup helper — returns undefined for unknown ids. */
export function getHomeEmployerById(id: string): HomeEmployer | undefined {
  return BY_ID.get(id);
}

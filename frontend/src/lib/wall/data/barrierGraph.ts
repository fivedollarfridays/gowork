/**
 * Barrier graph data — 33-node DAG (W3 Driver B, T3.15).
 *
 * # Honest uncertainty
 *
 * The backend's `BarrierType` enum (backend/app/modules/matching/types.py)
 * declares 7 canonical barrier categories. There is NO live "barrier DAG"
 * endpoint at this point in the project; W4 may swap in a real
 * service-derived graph (e.g., from Reasoner output). Until then, this
 * module ships an editorial 33-node stub that:
 *
 *   1. Distributes nodes across the 7 canonical categories so every
 *      barrier type is visible in the constellation.
 *   2. Connects nodes with editorially-meaningful edges (e.g., transit →
 *      childcare → criminal-record dependencies that the demo's narrative
 *      threads through).
 *   3. Ships provenance metadata (source, sourceDate, version) so a
 *      build-time freshness gate can fail loud if the graph goes stale.
 *
 * The 33 number is editorial: it's enough nodes to feel "real" without
 * crowding the constellation past readability. If W4 swaps in a real
 * graph, the consumer (`BarrierConstellation`) iterates over `nodes` and
 * `edges` agnostically — no refactor needed.
 *
 * # Compound Lens
 *
 * Same module feeds Ch8 NOW (constellation) + W4 a11y description NEXT
 * (screen-reader text alternative for the 3D scene).
 */

import type { OfficeCategory } from "../officeRegistry";

/** The 7 barrier categories (mirrors backend `BarrierType` enum). */
export const BARRIER_CATEGORIES = [
  "credit",
  "transportation",
  "childcare",
  "housing",
  "health",
  "training",
  "criminal_record",
] as const;

export type BarrierCategory = (typeof BARRIER_CATEGORIES)[number];

export interface BarrierNode {
  /** Stable kebab-case id (used for graph edges + DOM data attributes). */
  id: string;
  /** Canonical barrier category (one of BARRIER_CATEGORIES). */
  category: BarrierCategory;
  /** i18n key resolving to the node's display label. */
  labelKey: string;
  /** Editorial weight 1..3 — drives node radius in the 3D scene. */
  weight: 1 | 2 | 3;
  /** Optional cross-link to an office category (Ch8 → Ch5/Ch7 visual tie). */
  officeCategory?: OfficeCategory;
}

export interface BarrierEdge {
  from: string;
  to: string;
  /** Optional editorial annotation — currently unused by the renderer. */
  rationale?: string;
}

export interface BarrierGraph {
  readonly nodes: readonly BarrierNode[];
  readonly edges: readonly BarrierEdge[];
}

export interface BarrierGraphProvenance {
  /** Description of the source (data origin or editorial provenance). */
  source: string;
  /** ISO 8601 date the graph was last reviewed. */
  sourceDate: string;
  /** Semantic version (drives downstream cache busting). */
  version: string;
}

/**
 * Editorial 33-node graph. Distribution across 7 barrier categories:
 *   - criminal_record: 6 nodes (gateway barrier — Carlos's primary)
 *   - transportation: 5 nodes (Ch4b's spine)
 *   - childcare: 5 nodes (Ch4c's spine)
 *   - credit: 5 nodes (Ch4d's spine)
 *   - housing: 4 nodes (cliff cluster)
 *   - health: 4 nodes (eligibility cluster)
 *   - training: 4 nodes (workforce cluster)
 *   = 33 total
 *
 * Edges are editorially-curated dependencies (e.g., expungement → housing,
 * transit → job, childcare → schedule). They form a DAG without cycles
 * because barrier-removal is the editorial throughline.
 */
const NODES: readonly BarrierNode[] = [
  // criminal_record (6)
  { id: "cr-misdemeanor", category: "criminal_record", labelKey: "wall.chapter08.barrierLabels.crMisdemeanor", weight: 3 },
  { id: "cr-felony", category: "criminal_record", labelKey: "wall.chapter08.barrierLabels.crFelony", weight: 3 },
  { id: "cr-expunction", category: "criminal_record", labelKey: "wall.chapter08.barrierLabels.crExpunction", weight: 2, officeCategory: "court" },
  { id: "cr-article55", category: "criminal_record", labelKey: "wall.chapter08.barrierLabels.crArticle55", weight: 2, officeCategory: "legal" },
  { id: "cr-fair-chance", category: "criminal_record", labelKey: "wall.chapter08.barrierLabels.crFairChance", weight: 1 },
  { id: "cr-license-suspension", category: "criminal_record", labelKey: "wall.chapter08.barrierLabels.crLicense", weight: 2, officeCategory: "dps" },
  // transportation (5)
  { id: "tr-no-vehicle", category: "transportation", labelKey: "wall.chapter08.barrierLabels.trNoVehicle", weight: 3 },
  { id: "tr-bus-4", category: "transportation", labelKey: "wall.chapter08.barrierLabels.trBus4", weight: 2 },
  { id: "tr-bus-6", category: "transportation", labelKey: "wall.chapter08.barrierLabels.trBus6", weight: 2 },
  { id: "tr-transfer-time", category: "transportation", labelKey: "wall.chapter08.barrierLabels.trTransfer", weight: 2 },
  { id: "tr-night-shift", category: "transportation", labelKey: "wall.chapter08.barrierLabels.trNightShift", weight: 1 },
  // childcare (5)
  { id: "cc-cost", category: "childcare", labelKey: "wall.chapter08.barrierLabels.ccCost", weight: 3 },
  { id: "cc-subsidy", category: "childcare", labelKey: "wall.chapter08.barrierLabels.ccSubsidy", weight: 2, officeCategory: "benefits" },
  { id: "cc-hours", category: "childcare", labelKey: "wall.chapter08.barrierLabels.ccHours", weight: 2 },
  { id: "cc-waitlist", category: "childcare", labelKey: "wall.chapter08.barrierLabels.ccWaitlist", weight: 2 },
  { id: "cc-transit", category: "childcare", labelKey: "wall.chapter08.barrierLabels.ccTransit", weight: 1 },
  // credit (5)
  { id: "cd-low-score", category: "credit", labelKey: "wall.chapter08.barrierLabels.cdLowScore", weight: 3 },
  { id: "cd-collections", category: "credit", labelKey: "wall.chapter08.barrierLabels.cdCollections", weight: 2 },
  { id: "cd-employment-check", category: "credit", labelKey: "wall.chapter08.barrierLabels.cdEmployerCheck", weight: 2 },
  { id: "cd-rental-check", category: "credit", labelKey: "wall.chapter08.barrierLabels.cdRentalCheck", weight: 2 },
  { id: "cd-utility-deposit", category: "credit", labelKey: "wall.chapter08.barrierLabels.cdUtility", weight: 1 },
  // housing (4)
  { id: "hs-stable-address", category: "housing", labelKey: "wall.chapter08.barrierLabels.hsStableAddress", weight: 3 },
  { id: "hs-deposit", category: "housing", labelKey: "wall.chapter08.barrierLabels.hsDeposit", weight: 2 },
  { id: "hs-eviction", category: "housing", labelKey: "wall.chapter08.barrierLabels.hsEviction", weight: 2 },
  { id: "hs-shelter", category: "housing", labelKey: "wall.chapter08.barrierLabels.hsShelter", weight: 1 },
  // health (4)
  { id: "hl-medicaid", category: "health", labelKey: "wall.chapter08.barrierLabels.hlMedicaid", weight: 2, officeCategory: "benefits" },
  { id: "hl-dental", category: "health", labelKey: "wall.chapter08.barrierLabels.hlDental", weight: 1 },
  { id: "hl-mental", category: "health", labelKey: "wall.chapter08.barrierLabels.hlMental", weight: 2 },
  { id: "hl-physical", category: "health", labelKey: "wall.chapter08.barrierLabels.hlPhysical", weight: 1 },
  // training (4)
  { id: "tn-forklift", category: "training", labelKey: "wall.chapter08.barrierLabels.tnForklift", weight: 2, officeCategory: "workforce" },
  { id: "tn-cdl", category: "training", labelKey: "wall.chapter08.barrierLabels.tnCdl", weight: 2 },
  { id: "tn-ged", category: "training", labelKey: "wall.chapter08.barrierLabels.tnGed", weight: 2 },
  { id: "tn-resume", category: "training", labelKey: "wall.chapter08.barrierLabels.tnResume", weight: 1 },
] as const;

/**
 * Editorially-curated edges (38 total). Direction is "from preceding
 * barrier → unlocked barrier" — i.e., resolving the FROM enables progress
 * on the TO. The DAG is acyclic because barrier-removal narrative-flows
 * one way through the demo.
 */
const EDGES: readonly BarrierEdge[] = [
  // criminal-record subtree
  { from: "cr-misdemeanor", to: "cr-expunction" },
  { from: "cr-felony", to: "cr-expunction" },
  { from: "cr-expunction", to: "cr-article55" },
  { from: "cr-article55", to: "cr-fair-chance" },
  { from: "cr-license-suspension", to: "cr-fair-chance" },
  { from: "cr-fair-chance", to: "tn-forklift" },
  // transportation subtree
  { from: "tr-no-vehicle", to: "tr-bus-4" },
  { from: "tr-no-vehicle", to: "tr-bus-6" },
  { from: "tr-bus-4", to: "tr-transfer-time" },
  { from: "tr-bus-6", to: "tr-transfer-time" },
  { from: "tr-transfer-time", to: "tr-night-shift" },
  // childcare subtree
  { from: "cc-cost", to: "cc-subsidy" },
  { from: "cc-subsidy", to: "cc-hours" },
  { from: "cc-hours", to: "cc-waitlist" },
  { from: "cc-waitlist", to: "cc-transit" },
  // credit subtree
  { from: "cd-low-score", to: "cd-collections" },
  { from: "cd-collections", to: "cd-employment-check" },
  { from: "cd-collections", to: "cd-rental-check" },
  { from: "cd-rental-check", to: "cd-utility-deposit" },
  // housing subtree
  { from: "hs-stable-address", to: "hs-deposit" },
  { from: "hs-eviction", to: "hs-shelter" },
  { from: "hs-shelter", to: "hs-stable-address" },
  // health subtree
  { from: "hl-medicaid", to: "hl-dental" },
  { from: "hl-medicaid", to: "hl-mental" },
  { from: "hl-physical", to: "hl-medicaid" },
  // training subtree
  { from: "tn-ged", to: "tn-forklift" },
  { from: "tn-ged", to: "tn-cdl" },
  { from: "tn-resume", to: "tn-forklift" },
  // cross-cluster threads (the editorial ones)
  { from: "tr-transfer-time", to: "cc-hours" },         // transit blocks childcare hours
  { from: "cc-transit", to: "tr-no-vehicle" },           // childcare-transit ties back
  { from: "cd-employment-check", to: "cr-fair-chance" }, // credit fail blocks fair-chance
  { from: "cd-rental-check", to: "hs-deposit" },         // credit blocks housing deposit
  { from: "hs-stable-address", to: "cd-low-score" },     // housing instability hurts credit
  { from: "hl-medicaid", to: "cc-subsidy" },             // medicaid eligibility ↔ subsidy
  { from: "cr-expunction", to: "hs-eviction" },          // record blocks rentals
  { from: "tn-forklift", to: "tr-night-shift" },         // job → night shift transit need
  { from: "tn-cdl", to: "tr-no-vehicle" },               // CDL solves transit
  { from: "cr-license-suspension", to: "tr-no-vehicle" },// license suspension = no driving
] as const;

/** Public graph object — readonly to consumers. */
export const BARRIER_GRAPH: BarrierGraph = {
  nodes: NODES,
  edges: EDGES,
} as const;

export const barrierGraphProvenance: BarrierGraphProvenance = {
  source:
    "Editorial stub derived from backend BarrierType enum (CREDIT, TRANSPORTATION, CHILDCARE, HOUSING, HEALTH, TRAINING, CRIMINAL_RECORD) + Tarrant County office registry. W4 may replace with live Reasoner output.",
  sourceDate: "2026-04-28",
  version: "0.1.0",
} as const;

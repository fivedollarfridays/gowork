/**
 * Jobs-by-ZIP employer data — extracted to its own module so the
 * `jobsByZip.ts` layer file stays under the 15-functions architecture
 * limit and 200-line warning.
 *
 * # Provenance + honest uncertainty
 *
 * Fair-chance flags are educated approximations based on publicly
 * available employer hiring statements (e.g., Amazon's published
 * second-chance hiring program; Walmart's Open Doors policy). Where the
 * employer has no public statement, `fairChance: false` is the
 * conservative default. Submission ships with this honest baseline; a
 * follow-up curation task (W4) can refine flags from primary sources.
 *
 * # W3 Ch6 hard requirement
 *
 * The `id: "amazon-dfw5"` entry is consumed by W3 Ch6 (camera flies to
 * Amazon FC DFW5). The id + coords are locked here in W2.
 */

export interface EmployerPoint {
  id: string;
  name: string;
  category: "warehouse" | "retail" | "logistics" | "healthcare" | "manufacturing" | "service";
  fairChance: boolean;
  creditCheck: boolean;
  longitude: number;
  latitude: number;
}

export const JOBS_BY_ZIP_EMPLOYERS: readonly EmployerPoint[] = [
  // W3 Ch6 anchor — Amazon FC DFW5 near Alliance Airport.
  {
    id: "amazon-dfw5",
    name: "Amazon Fulfillment Center DFW5",
    category: "warehouse",
    fairChance: true,
    creditCheck: false,
    longitude: -97.3198,
    latitude: 32.9922,
  },
  // Warehouse / logistics cluster (Bus 4 / I-820 corridor).
  {
    id: "fedex-fw-distribution",
    name: "FedEx Ground — Fort Worth Distribution",
    category: "logistics",
    fairChance: true,
    creditCheck: false,
    longitude: -97.265,
    latitude: 32.795,
  },
  {
    id: "ups-fw-hub",
    name: "UPS Fort Worth Hub",
    category: "logistics",
    fairChance: true,
    creditCheck: false,
    longitude: -97.286,
    latitude: 32.812,
  },
  {
    id: "xpo-logistics-fw",
    name: "XPO Logistics — Fort Worth",
    category: "logistics",
    fairChance: false,
    creditCheck: false,
    longitude: -97.341,
    latitude: 32.78,
  },
  {
    id: "saia-freight-fw",
    name: "Saia Freight — Fort Worth Terminal",
    category: "logistics",
    fairChance: false,
    creditCheck: false,
    longitude: -97.298,
    latitude: 32.808,
  },
  // Manufacturing.
  {
    id: "lockheed-martin-fw",
    name: "Lockheed Martin Aeronautics — Fort Worth",
    category: "manufacturing",
    fairChance: false,
    creditCheck: true,
    longitude: -97.4396,
    latitude: 32.7707,
  },
  {
    id: "bell-textron-fw",
    name: "Bell Textron — Fort Worth",
    category: "manufacturing",
    fairChance: false,
    creditCheck: true,
    longitude: -97.358,
    latitude: 32.84,
  },
  {
    id: "hilton-foods-fw",
    name: "Hilton Foods Group — Fort Worth Plant",
    category: "manufacturing",
    fairChance: true,
    creditCheck: false,
    longitude: -97.31,
    latitude: 32.69,
  },
  // Retail (warehouse / fulfillment ops).
  {
    id: "walmart-dc-grand-prairie",
    name: "Walmart Distribution Center — Grand Prairie",
    category: "warehouse",
    fairChance: true,
    creditCheck: false,
    longitude: -97.21,
    latitude: 32.736,
  },
  {
    id: "target-dc-fw",
    name: "Target Distribution — Fort Worth",
    category: "warehouse",
    fairChance: true,
    creditCheck: false,
    longitude: -97.25,
    latitude: 32.84,
  },
  {
    id: "home-depot-fw",
    name: "Home Depot — Fort Worth",
    category: "retail",
    fairChance: true,
    creditCheck: false,
    longitude: -97.36,
    latitude: 32.71,
  },
  {
    id: "lowes-fw",
    name: "Lowe's — Fort Worth",
    category: "retail",
    fairChance: true,
    creditCheck: false,
    longitude: -97.4,
    latitude: 32.77,
  },
  {
    id: "kroger-fw-east",
    name: "Kroger — East Fort Worth",
    category: "retail",
    fairChance: true,
    creditCheck: false,
    longitude: -97.27,
    latitude: 32.745,
  },
  {
    id: "albertsons-fw",
    name: "Albertsons — Fort Worth",
    category: "retail",
    fairChance: false,
    creditCheck: false,
    longitude: -97.42,
    latitude: 32.72,
  },
  // Healthcare (often does background + credit checks for clinical roles).
  {
    id: "texas-health-fw",
    name: "Texas Health Harris Methodist — Fort Worth",
    category: "healthcare",
    fairChance: false,
    creditCheck: true,
    longitude: -97.336,
    latitude: 32.752,
  },
  {
    id: "jps-health-network",
    name: "JPS Health Network",
    category: "healthcare",
    fairChance: true,
    creditCheck: false,
    longitude: -97.339,
    latitude: 32.745,
  },
  {
    id: "cooks-childrens",
    name: "Cook Children's Medical Center",
    category: "healthcare",
    fairChance: false,
    creditCheck: true,
    longitude: -97.348,
    latitude: 32.74,
  },
  {
    id: "baylor-scott-white-fw",
    name: "Baylor Scott & White — Fort Worth",
    category: "healthcare",
    fairChance: false,
    creditCheck: true,
    longitude: -97.385,
    latitude: 32.756,
  },
  // Service.
  {
    id: "marriott-fw-downtown",
    name: "Fort Worth Marriott Downtown",
    category: "service",
    fairChance: true,
    creditCheck: false,
    longitude: -97.327,
    latitude: 32.749,
  },
  {
    id: "hilton-fw",
    name: "Hilton Fort Worth",
    category: "service",
    fairChance: false,
    creditCheck: false,
    longitude: -97.334,
    latitude: 32.751,
  },
  {
    id: "omni-fw-hotel",
    name: "Omni Fort Worth Hotel",
    category: "service",
    fairChance: false,
    creditCheck: true,
    longitude: -97.338,
    latitude: 32.749,
  },
  {
    id: "starbucks-fw-roastery",
    name: "Starbucks Roastery — Fort Worth",
    category: "service",
    fairChance: true,
    creditCheck: false,
    longitude: -97.343,
    latitude: 32.732,
  },
  {
    id: "chipotle-fw-east",
    name: "Chipotle — East Fort Worth",
    category: "service",
    fairChance: true,
    creditCheck: false,
    longitude: -97.295,
    latitude: 32.728,
  },
  {
    id: "mcdonalds-berry",
    name: "McDonald's — E Berry St",
    category: "service",
    fairChance: true,
    creditCheck: false,
    longitude: -97.288,
    latitude: 32.715,
  },
  // More warehouse / distribution to round out the 30+ requirement.
  {
    id: "performance-foodservice",
    name: "Performance Foodservice — Fort Worth",
    category: "logistics",
    fairChance: true,
    creditCheck: false,
    longitude: -97.302,
    latitude: 32.79,
  },
  {
    id: "sysco-fw",
    name: "Sysco Fort Worth",
    category: "logistics",
    fairChance: true,
    creditCheck: false,
    longitude: -97.27,
    latitude: 32.83,
  },
  {
    id: "tyson-foods-fw",
    name: "Tyson Foods — Fort Worth Plant",
    category: "manufacturing",
    fairChance: true,
    creditCheck: false,
    longitude: -97.305,
    latitude: 32.685,
  },
  {
    id: "frito-lay-fw",
    name: "Frito-Lay — Fort Worth",
    category: "manufacturing",
    fairChance: false,
    creditCheck: false,
    longitude: -97.41,
    latitude: 32.81,
  },
  {
    id: "alcon-fw",
    name: "Alcon Laboratories — Fort Worth",
    category: "manufacturing",
    fairChance: false,
    creditCheck: true,
    longitude: -97.305,
    latitude: 32.79,
  },
  {
    id: "amerisourcebergen-fw",
    name: "AmerisourceBergen — Fort Worth",
    category: "logistics",
    fairChance: true,
    creditCheck: false,
    longitude: -97.31,
    latitude: 32.778,
  },
  {
    id: "americold-fw",
    name: "Americold Logistics — Fort Worth",
    category: "warehouse",
    fairChance: true,
    creditCheck: false,
    longitude: -97.28,
    latitude: 32.77,
  },
  {
    id: "geodis-fw",
    name: "GEODIS Logistics — Fort Worth",
    category: "logistics",
    fairChance: false,
    creditCheck: false,
    longitude: -97.27,
    latitude: 32.808,
  },
] as const;

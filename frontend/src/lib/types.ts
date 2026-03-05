/* MontGoWork shared TypeScript types — mirrors backend Pydantic models */

// --- Enums ---

export const BarrierType = {
  CREDIT: "credit",
  TRANSPORTATION: "transportation",
  CHILDCARE: "childcare",
  HOUSING: "housing",
  HEALTH: "health",
  TRAINING: "training",
  CRIMINAL_RECORD: "criminal_record",
} as const;
export type BarrierType = (typeof BarrierType)[keyof typeof BarrierType];

export const BarrierSeverity = {
  HIGH: "high",
  MEDIUM: "medium",
  LOW: "low",
} as const;
export type BarrierSeverity = (typeof BarrierSeverity)[keyof typeof BarrierSeverity];

export const EmploymentStatus = {
  UNEMPLOYED: "unemployed",
  UNDEREMPLOYED: "underemployed",
  SEEKING_CHANGE: "seeking_change",
} as const;
export type EmploymentStatus = (typeof EmploymentStatus)[keyof typeof EmploymentStatus];

export const AvailableHours = {
  DAYTIME: "daytime",
  EVENING: "evening",
  NIGHT: "night",
  FLEXIBLE: "flexible",
} as const;
export type AvailableHours = (typeof AvailableHours)[keyof typeof AvailableHours];

export const CrawlStatus = {
  PENDING: "pending",
  RUNNING: "running",
  COMPLETE: "complete",
  FAILED: "failed",
} as const;
export type CrawlStatus = (typeof CrawlStatus)[keyof typeof CrawlStatus];

// --- Models ---

export interface ScheduleConstraints {
  available_days: string[];
  available_hours: AvailableHours;
}

export interface AssessmentRequest {
  zip_code: string;
  employment_status: EmploymentStatus;
  barriers: Record<BarrierType, boolean>;
  work_history: string;
  target_industries: string[];
  has_vehicle: boolean;
  schedule_constraints: ScheduleConstraints;
}

export interface UserProfile {
  session_id: string;
  zip_code: string;
  employment_status: EmploymentStatus;
  barrier_count: number;
  primary_barriers: BarrierType[];
  barrier_severity: BarrierSeverity;
  needs_credit_assessment: boolean;
  transit_dependent: boolean;
  schedule_type: string;
  work_history: string;
  target_industries: string[];
}

export interface Resource {
  id: number;
  name: string;
  category: string;
  subcategory: string | null;
  address: string | null;
  phone: string | null;
  url: string | null;
  eligibility: string | null;
  services: string[] | null;
  notes: string | null;
}

export interface JobMatch {
  title: string;
  company: string | null;
  location: string | null;
  url: string | null;
  source: string | null;
  transit_accessible: boolean;
  route: string | null;
  credit_check_required: string;
  eligible_now: boolean;
  eligible_after: string | null;
}

export interface TransitConnection {
  route_number: number;
  route_name: string;
  connects_to: string[];
  schedule: string;
}

export interface BarrierCard {
  type: BarrierType;
  severity: BarrierSeverity;
  title: string;
  timeline_days: number | null;
  actions: string[];
  resources: Resource[];
  transit_matches: TransitConnection[];
}

export interface ReEntryPlan {
  plan_id: string;
  session_id: string;
  resident_summary: string | null;
  barriers: BarrierCard[];
  job_matches: JobMatch[];
  immediate_next_steps: string[];
  credit_readiness_score: number | null;
  eligible_now: string[];
  eligible_after_repair: string[];
}

export interface AssessmentResponse {
  session_id: string;
  profile: UserProfile;
  plan: ReEntryPlan;
}

export interface PlanResponse {
  session_id: string;
  barriers: string[];
  qualifications: string | null;
  plan: ReEntryPlan | null;
}

export interface PlanNarrative {
  summary: string;
  key_actions: string[];
}

export interface JobsResponse {
  jobs: EnrichedJob[];
  total: number;
}

export interface EnrichedJob {
  id: number;
  title: string;
  company: string | null;
  url: string | null;
  source: string | null;
  scraped_at: string | null;
  industry: string | null;
  credit_check_required: string;
  transit_info: TransitInfo | null;
  application_steps: string[];
}

export interface TransitInfo {
  accessible: boolean;
  routes: { route_number: number; route_name: string }[];
  schedule: string;
}

// --- Credit types ---

export interface AccountSummary {
  total_accounts: number;
  open_accounts: number;
  closed_accounts: number;
  negative_accounts: number;
  collection_accounts: number;
  total_balance: number;
  total_credit_limit: number;
  monthly_payments: number;
}

export interface CreditProfileRequest {
  current_score: number;
  score_band: string | null;
  overall_utilization: number;
  account_summary: AccountSummary;
  payment_history_pct: number;
  average_account_age_months: number;
  negative_items: string[];
}

export interface CreditReadiness {
  score: number;
  fico_score: number;
  score_band: string;
  factors: {
    payment_history: number;
    utilization: number;
    credit_age: number;
    credit_mix: number;
    new_credit: number;
  };
}

export interface CreditThreshold {
  threshold_name: string;
  threshold_score: number;
  estimated_days: number;
  already_met: boolean;
  confidence: string;
}

export interface DisputeStep {
  step_number: number;
  action: string;
  description: string;
}

export interface DisputePathway {
  steps: DisputeStep[];
  total_estimated_days: number;
  statutes_cited: string[];
  legal_theories: string[];
}

export interface CreditEligibility {
  product_name: string;
  category: string;
  required_score: number;
  status: string;
  gap_points: number;
  estimated_days_to_eligible: number;
}

export interface BarrierDetail {
  severity: string;
  description: string;
  affected_accounts: string[];
  estimated_resolution_days: number;
}

export interface CreditAssessmentResult {
  barrier_severity: string;
  barrier_details: BarrierDetail[];
  readiness: CreditReadiness;
  thresholds: CreditThreshold[];
  dispute_pathway: DisputePathway;
  eligibility: CreditEligibility[];
  disclaimer: string;
}

export interface CreditFormData {
  currentScore: number;
  overallUtilization: number;
  paymentHistoryPct: number;
  accountAgeRange: string;
  totalAccounts: number;
  openAccounts: number;
  collectionAccounts: number;
  negativeItems: string[];
}

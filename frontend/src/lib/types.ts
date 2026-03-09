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

// --- Criminal Record types ---

export const RecordType = {
  FELONY: "felony",
  MISDEMEANOR: "misdemeanor",
  ARREST_ONLY: "arrest_only",
  EXPUNGED: "expunged",
} as const;
export type RecordType = (typeof RecordType)[keyof typeof RecordType];

export const ChargeCategory = {
  VIOLENCE: "violence",
  THEFT: "theft",
  DRUG: "drug",
  DUI: "dui",
  SEX_OFFENSE: "sex_offense",
  FRAUD: "fraud",
  OTHER: "other",
} as const;
export type ChargeCategory = (typeof ChargeCategory)[keyof typeof ChargeCategory];

export interface RecordProfile {
  record_types: RecordType[];
  charge_categories: ChargeCategory[];
  years_since_conviction: number | null;
  completed_sentence: boolean;
}

// --- Models ---

export interface ScheduleConstraints {
  available_days: string[];
  available_hours: AvailableHours;
}

export interface BenefitsFormData {
  household_size: number;
  current_monthly_income: number;
  enrolled_programs: string[];
  dependents_under_6: number;
  dependents_6_to_17: number;
}

export interface AssessmentRequest {
  zip_code: string;
  employment_status: EmploymentStatus;
  barriers: Record<BarrierType, boolean>;
  work_history: string;
  target_industries: string[];
  has_vehicle: boolean;
  schedule_constraints: ScheduleConstraints;
  resume_text?: string;
  certifications?: string[];
  credit_result?: CreditAssessmentResult;
  record_profile?: RecordProfile;
  benefits_data?: BenefitsFormData;
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
  record_profile: RecordProfile | null;
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
  health_status?: ResourceHealth;
  eligibility_status?: "likely" | "check" | null;
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
  fair_chance?: boolean;
  record_eligible?: boolean;
  background_check_timing?: string | null;
  record_note?: string | null;
}

export type CliffSeverity = "mild" | "moderate" | "severe";

export interface CliffImpact {
  benefits_change: number;
  net_monthly_change: number;
  has_cliff: boolean;
  severity: CliffSeverity | null;
  affected_programs: string[];
}

export interface ScoredJobMatch extends JobMatch {
  relevance_score: number;
  match_reason: string;
  bucket: "strong" | "possible" | "after_repair";
  pay_range?: string | null;
  cliff_impact?: CliffImpact | null;
  fair_chance?: boolean;
  employment_type?: string | null;
  transit_info?: TransitInfoDetail | null;
}

export interface WageStep {
  wage: number;
  gross_monthly: number;
  benefits_total: number;
  net_monthly: number;
}

export interface CliffPoint {
  hourly_wage: number;
  annual_income: number;
  net_monthly_income: number;
  lost_program: string;
  monthly_loss: number;
  severity: CliffSeverity;
}

export interface CliffAnalysis {
  wage_steps: WageStep[];
  cliff_points: CliffPoint[];
  current_net_monthly: number;
  programs: { program: string; monthly_value: number; eligible: boolean }[];
  worst_cliff_wage: number | null;
  recovery_wage: number | null;
}

export interface TransitConnection {
  route_number: number;
  route_name: string;
  connects_to: string[];
  schedule: string;
}

export type ExpungementEligibility = "eligible_now" | "eligible_future" | "not_eligible" | "unknown";

export interface ExpungementResult {
  eligibility: ExpungementEligibility;
  years_remaining: number | null;
  steps: string[];
  filing_fee: string | null;
  notes: string | null;
}

export interface BarrierCard {
  type: BarrierType;
  severity: BarrierSeverity;
  title: string;
  timeline_days: number | null;
  actions: string[];
  resources: Resource[];
  transit_matches: TransitConnection[];
  expungement?: ExpungementResult | null;
}

export type ReadinessBand = "not_ready" | "developing" | "ready" | "strong";

export interface ReadinessFactor {
  name: string;
  weight: number;
  score: number;
  detail: string;
}

export interface ReadinessPathwayStep {
  step_number: number;
  action: string;
  resource: string;
  timeline_days: number;
  completed: boolean;
}

export interface JobReadinessResult {
  overall_score: number;
  readiness_band: ReadinessBand;
  factors: ReadinessFactor[];
  pathway: ReadinessPathwayStep[];
  estimated_days_to_ready: number;
  summary: string;
}

export interface WIOAEligibility {
  adult_program: boolean;
  adult_reasons: string[];
  supportive_services: boolean;
  ita_training: boolean;
  dislocated_worker: string;
  confidence: string;
}

export type EligibilityConfidence = "likely" | "possible" | "unlikely";

export interface ProgramApplicationInfo {
  application_url: string;
  application_steps: string[];
  required_documents: string[];
  office_name: string;
  office_address: string;
  office_phone: string;
  processing_time: string;
}

export interface ProgramEligibility {
  program: string;
  eligible: boolean;
  confidence: EligibilityConfidence;
  income_threshold: number;
  income_headroom: number;
  estimated_monthly_value: number;
  reason: string;
  application_info?: ProgramApplicationInfo | null;
}

export interface BenefitsEligibility {
  eligible_programs: ProgramEligibility[];
  ineligible_programs: ProgramEligibility[];
  total_estimated_monthly: number;
  disclaimer: string;
}

export interface ReEntryPlan {
  plan_id: string;
  session_id: string;
  resident_summary: string | null;
  barriers: BarrierCard[];
  job_matches: ScoredJobMatch[];  // computed: strong + possible + after_repair
  strong_matches: ScoredJobMatch[];
  possible_matches: ScoredJobMatch[];
  after_repair: ScoredJobMatch[];
  immediate_next_steps: string[];
  credit_readiness_score: number | null;
  eligible_now: string[];
  eligible_after_repair: string[];
  wioa_eligibility: WIOAEligibility | null;
  job_readiness: JobReadinessResult | null;
  benefits_cliff_analysis?: CliffAnalysis | null;
  benefits_eligibility?: BenefitsEligibility | null;
}

export interface AssessmentResponse {
  session_id: string;
  profile: UserProfile;
  plan: ReEntryPlan;
  feedback_token?: string;
}

export interface PlanResponse {
  session_id: string;
  barriers: string[];
  qualifications: string | null;
  plan: ReEntryPlan | null;
  credit_profile: CreditAssessmentResult | null;
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
  location: string | null;
  description: string | null;
  url: string | null;
  source: string | null;
  scraped_at: string | null;
  industry: string | null;
  credit_check_required: string;
  fair_chance: boolean;
  employment_type: string | null;
  transit_info: TransitInfo | null;
  application_steps: string[];
}

export type TransitWarning = "sunday_gap" | "night_gap" | "long_walk" | "transfer_required";

export interface RouteFeasibility {
  route_number: number;
  route_name: string;
  nearest_stop: string;
  walk_miles: number;
  first_bus: string;
  last_bus: string;
  has_sunday: boolean;
  feasible: boolean;
}

export interface TransitInfoDetail {
  serving_routes: RouteFeasibility[];
  transfer_count: number;
  warnings: TransitWarning[];
  google_maps_url: string | null;
}

/** @deprecated Use TransitInfoDetail for schedule-aware transit data */
export interface TransitInfo {
  accessible: boolean;
  routes: { route_number: number; route_name: string }[];
  schedule: string;
}

// --- Credit types ---

export interface CreditProfileRequest {
  credit_score: number;
  utilization_percent: number;
  total_accounts: number;
  open_accounts: number;
  negative_items: string[];
  payment_history_percent: number;
  oldest_account_months: number;
  total_balance?: number;
  total_credit_limit?: number;
  monthly_payments?: number;
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

// --- Feedback types ---

export const ResourceHealth = {
  HEALTHY: "healthy",
  WATCH: "watch",
  FLAGGED: "flagged",
  HIDDEN: "hidden",
} as const;
export type ResourceHealth = (typeof ResourceHealth)[keyof typeof ResourceHealth];

export interface ResourceFeedbackRequest {
  resource_id: number;
  session_id: string;
  helpful: boolean;
  barrier_type?: string;
  token: string;
}

export interface ResourceFeedbackResponse {
  success: boolean;
  resource_id: number;
  helpful: boolean;
}

export interface VisitFeedbackRequest {
  token: string;
  made_it_to_center: number;
  outcomes: string[];
  plan_accuracy: number;
  free_text?: string;
}

export interface VisitFeedbackResponse {
  success: boolean;
}

export interface TokenValidation {
  valid: boolean;
  session_id?: string;
}

// --- Career Center Package types ---

export interface CareerCenterInfo {
  name: string;
  phone: string;
  address: string;
  hours: string;
  transit_route: string;
}

export interface DocumentChecklistItem {
  label: string;
  required: boolean;
}

export interface StaffSummary {
  employment_goal: string;
  barrier_profile: string[];
  wioa_eligibility: WIOAEligibility | null;
  staff_next_steps: string[];
}

export interface ResidentActionPlan {
  document_checklist: DocumentChecklistItem[];
  work_history: string;
  what_to_say: string[];
  what_to_expect: string[];
  career_center: CareerCenterInfo;
  programs: string[];
}

export interface CreditPathway {
  blocking: string[];
  not_blocking: string[];
  dispute_steps: string[];
  free_resources: string[];
}

export interface CareerCenterPackage {
  staff_summary: StaffSummary;
  resident_plan: ResidentActionPlan;
  credit_pathway: CreditPathway | null;
  generated_at: string;
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

// --- Barrier Intelligence types ---

export type ChatMode = "next_steps" | "explain_plan";

export interface ExplainStep {
  text: string;
  reasoning?: string;
}

export interface EvidenceSource {
  name: string;
  resource_id?: number;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  context?: ChatContext;
  steps?: ExplainStep[];
  evidence?: EvidenceSource[];
  disclaimer?: string;
}

export interface ChatContext {
  root_barriers: string[];
  chain: string;
}

export interface ChatSSEEvent {
  type: "context" | "token" | "done" | "disclaimer";
  root_barriers?: string[];
  chain?: string;
  text?: string;
  chunks?: number;
  latency_ms?: number;
}

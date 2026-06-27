export type BudgetType = "fixed" | "hourly";

export type JobStatus =
  | "new"
  | "shortlisted"
  | "applied"
  | "ignored"
  | "archived";

export interface Job {
  id: string;
  user_id: string;
  title: string;
  description: string;
  source_url: string | null;
  budget_type: BudgetType | null;
  budget_min: string | null;
  budget_max: string | null;
  currency: string;
  proposal_count: number | null;
  client_id: string | null;
  status: JobStatus;
  source_hash: string;
  version: number;
  imported_at: string;
  created_at: string;
  updated_at: string;
}

export interface JobListResponse {
  items: Job[];
  total: number;
  limit: number;
  offset: number;
}

export interface JobCreate {
  title: string;
  description: string;
  source_url?: string | null;
  budget_type?: BudgetType | null;
  budget_min?: number | null;
  budget_max?: number | null;
  currency?: string;
  proposal_count?: number | null;
}

export type JobUpdate = Partial<JobCreate & { status: JobStatus }>;

export type Complexity = "low" | "medium" | "high";
export type RiskLevel = "low" | "medium" | "high";
export type Severity = "low" | "medium" | "high";
export type Seniority = "junior" | "mid" | "senior" | "lead" | "staff" | "principal";
export type BudgetAssessment = "low" | "reasonable" | "high" | "unclear";
export type Recommendation = "Strong Apply" | "Apply" | "Maybe" | "Skip";
export type Confidence = "high" | "medium" | "low";

export interface RiskItem {
  risk: string;
  severity: Severity;
  mitigation: string;
}

export interface JobAnalysis {
  id: string;
  job_id: string;
  summary: string | null;
  required_skills: string[];
  preferred_skills: string[];
  technologies: string[];
  business_domain: string | null;
  seniority: string | null;
  complexity: Complexity | null;
  estimated_hours_min: number | null;
  estimated_hours_max: number | null;
  budget_assessment: BudgetAssessment | null;
  client_intent: string | null;
  hidden_requirements: string[];
  expected_deliverables: string[];
  risks: RiskItem[];
  red_flags: string[];
  green_flags: string[];
  questions_to_ask_client: string[];
  risk_level: RiskLevel | null;
  communication_required: string | null;
  provider: string | null;
  model: string | null;
  prompt_version: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface ScoreBreakdown {
  technical_fit: number;
  domain_fit: number;
  proposal_count: number;
  budget_attractiveness: number;
  client_quality: number;
  estimated_effort: number;
  risk_level: number;
  strategic_value: number;
}

export interface OpportunityScore {
  id: string;
  job_id: string;
  analysis_id: string;
  score: number;
  recommendation: Recommendation;
  confidence: Confidence;
  score_breakdown: ScoreBreakdown;
  reasoning: string;
  profile_version: string;
  created_at: string | null;
  updated_at: string | null;
}

export interface JobAnalysisResponse {
  analysis: JobAnalysis;
  score: OpportunityScore;
}

export const SCORE_DIMENSION_LABELS: Record<keyof ScoreBreakdown, string> = {
  technical_fit: "Technical fit",
  domain_fit: "Domain fit",
  proposal_count: "Proposal count",
  budget_attractiveness: "Budget",
  client_quality: "Client quality",
  estimated_effort: "Effort",
  risk_level: "Risk",
  strategic_value: "Strategic value",
};

export const SCORE_DIMENSION_MAX: Record<keyof ScoreBreakdown, number> = {
  technical_fit: 25,
  domain_fit: 10,
  proposal_count: 20,
  budget_attractiveness: 10,
  client_quality: 10,
  estimated_effort: 10,
  risk_level: 10,
  strategic_value: 5,
};

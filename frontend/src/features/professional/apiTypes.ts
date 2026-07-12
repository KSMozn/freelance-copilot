export type BudgetType = "fixed" | "hourly";

export type JobStatus = "new" | "shortlisted" | "applied" | "ignored" | "archived";

export interface CompanyResearch {
  source_url: string;
  business_domain: string | null;
  product_summary: string | null;
  target_customers: string | null;
  existing_stack: string[];
  funding_signals: string | null;
  likely_architecture: string | null;
  personalization_hook: string | null;
  fetched_at: string | null;
}

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
  opportunity_score?: OpportunityScore | null;
  client_research?: CompanyResearch | null;
}

export type JobSortBy =
  | "created_at"
  | "title"
  | "score"
  | "score.technical_fit"
  | "score.domain_fit"
  | "score.proposal_count"
  | "score.budget_attractiveness"
  | "score.client_quality"
  | "score.estimated_effort"
  | "score.risk_level"
  | "score.strategic_value";

export type SortDir = "asc" | "desc";

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

export type StackCategory =
  | "tech_stack"
  | "architecture"
  | "cloud_platform"
  | "ai_llm"
  | "authentication"
  | "billing"
  | "integrations"
  | "database"
  | "devops"
  | "testing"
  | "deployment"
  | "security"
  | "nice_to_have";

export interface StackRequirement {
  category: StackCategory;
  name: string;
  importance: 1 | 2 | 3 | 4 | 5;
}

export const STACK_CATEGORY_LABELS: Record<StackCategory, string> = {
  tech_stack: "Tech stack",
  architecture: "Architecture",
  cloud_platform: "Cloud",
  ai_llm: "AI / LLM",
  authentication: "Authentication",
  billing: "Billing",
  integrations: "Integrations",
  database: "Database",
  devops: "DevOps",
  testing: "Testing",
  deployment: "Deployment",
  security: "Security",
  nice_to_have: "Nice to have",
};

export const STACK_CATEGORY_ORDER: StackCategory[] = [
  "tech_stack",
  "architecture",
  "database",
  "cloud_platform",
  "ai_llm",
  "authentication",
  "billing",
  "integrations",
  "devops",
  "testing",
  "deployment",
  "security",
  "nice_to_have",
];

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
  stack_requirements: StackRequirement[];
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

// --- Phase 3: Portfolio + matching ---

export interface Portfolio {
  id: string;
  user_id: string;
  title: string;
  short_description: string | null;
  long_description: string;
  role: string | null;
  business_domain: string | null;
  github_url: string | null;
  live_url: string | null;
  technologies: string[];
  skills: string[];
  features: string[];
  outcomes: string[];
  highlight: boolean;
  created_at: string | null;
  updated_at: string | null;
}

export interface PortfolioListResponse {
  items: Portfolio[];
  total: number;
  limit: number;
  offset: number;
}

export interface PortfolioCreate {
  title: string;
  long_description: string;
  short_description?: string | null;
  role?: string | null;
  business_domain?: string | null;
  github_url?: string | null;
  live_url?: string | null;
  technologies?: string[];
  skills?: string[];
  features?: string[];
  outcomes?: string[];
  highlight?: boolean;
}

export type PortfolioUpdate = Partial<PortfolioCreate>;

export interface PortfolioMatch {
  portfolio_id: string;
  title: string;
  match_score: number;
  semantic_score: number;
  skill_overlap_score: number;
  domain_overlap_score: number;
  strategic_score: number;
  match_reasons: string[];
  relevant_skills: string[];
  relevant_domains: string[];
  suggested_talking_points: string[];
}

export interface PortfolioMatchesResponse {
  job_id: string;
  matches: PortfolioMatch[];
  embedding_provider: string;
  embedding_model: string;
  portfolio_count: number;
}

// --- Phase 4: Resume library + recommendations ---

export interface Resume {
  id: string;
  user_id: string;
  title: string;
  target_role: string | null;
  summary: string | null;
  seniority_level: string | null;
  primary_skills: string[];
  secondary_skills: string[];
  industries: string[];
  domains: string[];
  achievements: string[];
  project_highlights: string[];
  keywords: string[];
  notes: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface ResumeListResponse {
  items: Resume[];
  total: number;
  limit: number;
  offset: number;
}

export interface ResumeCreate {
  title: string;
  target_role?: string | null;
  summary?: string | null;
  seniority_level?: Seniority | null;
  primary_skills?: string[];
  secondary_skills?: string[];
  industries?: string[];
  domains?: string[];
  achievements?: string[];
  project_highlights?: string[];
  keywords?: string[];
  notes?: string | null;
}

export type ResumeUpdate = Partial<ResumeCreate>;

export interface ResumeRecommendation {
  resume_id: string;
  title: string;
  match_score: number;
  semantic_score: number;
  skill_overlap_score: number;
  domain_overlap_score: number;
  seniority_alignment_score: number;
  fit_reasons: string[];
  relevant_skills: string[];
  missing_or_weak_skills: string[];
  suggested_positioning: string[];
}

export interface ResumeRecommendationsResponse {
  job_id: string;
  recommendations: ResumeRecommendation[];
  embedding_provider: string;
  embedding_model: string;
  resume_count: number;
}

// --- Phase 5: Proposal generator ---

export interface ProposalMilestone {
  name: string;
  description: string;
  estimated_hours: number | null;
}

export interface ProposalQualityBreakdown {
  specificity: number;
  relevance: number;
  portfolio_evidence: number;
  clarity: number;
  brevity: number;
  non_generic_wording: number;
  risk_awareness: number;
  call_to_action: number;
}

export const PROPOSAL_DIMENSION_LABELS: Record<keyof ProposalQualityBreakdown, string> = {
  specificity: "Specificity",
  relevance: "Relevance",
  portfolio_evidence: "Portfolio evidence",
  clarity: "Clarity",
  brevity: "Brevity",
  non_generic_wording: "Non-generic wording",
  risk_awareness: "Risk awareness",
  call_to_action: "Call to action",
};

export const PROPOSAL_DIMENSION_MAX: Record<keyof ProposalQualityBreakdown, number> = {
  specificity: 20,
  relevance: 20,
  portfolio_evidence: 15,
  clarity: 15,
  brevity: 10,
  non_generic_wording: 10,
  risk_awareness: 5,
  call_to_action: 5,
};

export type ProposalAngle =
  | "leadership"
  | "hands_on_coding"
  | "ai"
  | "architecture"
  | "fast_delivery"
  | "enterprise"
  | "startup_mindset";

export interface ProposalStrategy {
  angle: ProposalAngle;
  rationale: string;
  emphasis_points: string[];
}

export const PROPOSAL_ANGLE_LABELS: Record<ProposalAngle, string> = {
  leadership: "Leadership",
  hands_on_coding: "Hands-on coding",
  ai: "AI / LLM",
  architecture: "Architecture",
  fast_delivery: "Fast delivery",
  enterprise: "Enterprise",
  startup_mindset: "Startup mindset",
};

export interface ImplementationWeek {
  week: number;
  focus: string;
  summary: string;
  deliverables: string[];
}

export type ProposalDiagramKind = "system" | "sequence";

export interface ProposalDiagram {
  kind: ProposalDiagramKind;
  title: string;
  mermaid: string;
}

export interface Proposal {
  id: string;
  user_id: string;
  job_id: string;
  resume_id: string | null;
  portfolio_ids: string[];
  title: string | null;
  body: string;
  short_body: string | null;
  questions: string[];
  milestones: ProposalMilestone[];
  delivery_approach: string[];
  risk_notes: string[];
  quality_score: number | null;
  quality_breakdown: ProposalQualityBreakdown | null;
  quality_warnings: string[];
  strategy: ProposalStrategy | null;
  implementation_plan: ImplementationWeek[];
  diagrams: ProposalDiagram[];
  prompt_version: string | null;
  model_provider: string | null;
  model_name: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface ProposalUpdateRequest {
  title?: string | null;
  body?: string;
  short_body?: string | null;
  questions?: string[];
  milestones?: ProposalMilestone[];
  delivery_approach?: string[];
  risk_notes?: string[];
}

export interface ProposalReviewResult {
  quality_score: number;
  quality_breakdown: ProposalQualityBreakdown;
  warnings: string[];
}

// --- Phase 6: Application tracker ---

export type ApplicationStatus =
  | "draft"
  | "applied"
  | "viewed"
  | "interview"
  | "offer"
  | "won"
  | "rejected"
  | "withdrawn"
  | "completed";

export const APPLICATION_STATUS_ORDER: ApplicationStatus[] = [
  "draft",
  "applied",
  "viewed",
  "interview",
  "offer",
  "won",
  "completed",
  "rejected",
  "withdrawn",
];

export const TERMINAL_APPLICATION_STATUSES: ReadonlySet<ApplicationStatus> = new Set([
  "rejected",
  "withdrawn",
  "completed",
]);

export const APPLICATION_STATUS_TRANSITIONS: Record<ApplicationStatus, ApplicationStatus[]> = {
  draft: ["applied"],
  applied: ["viewed", "interview", "rejected", "withdrawn"],
  viewed: ["interview", "rejected", "withdrawn"],
  interview: ["offer", "rejected", "withdrawn"],
  offer: ["won", "rejected", "withdrawn"],
  won: ["completed"],
  rejected: [],
  withdrawn: [],
  completed: [],
};

export interface ApplicationSnapshotJob {
  id?: string;
  title: string;
  url: string | null;
  budget: string | null;
  proposal_count: number | null;
  status?: string;
}

export interface ApplicationSnapshotOpportunity {
  score: number;
  recommendation: string;
  confidence?: string;
  breakdown: Record<string, number>;
  profile_version?: string;
}

export interface ApplicationSnapshotProposal {
  id?: string;
  title: string | null;
  body: string;
  short_body: string | null;
  quality_score: number | null;
  quality_breakdown: Record<string, number>;
  prompt_version?: string | null;
  model_provider?: string | null;
  model_name?: string | null;
}

export interface ApplicationSnapshotResume {
  id: string;
  title: string;
  target_role: string | null;
  seniority_level?: string | null;
  primary_skills?: string[];
  suggested_positioning: string[];
}

export interface ApplicationSnapshotPortfolio {
  id: string;
  title: string;
  business_domain?: string | null;
  match_score: number | null;
  relevant_skills?: string[];
  talking_points: string[];
}

export interface ApplicationSnapshot {
  job: ApplicationSnapshotJob;
  opportunity_score: ApplicationSnapshotOpportunity | null;
  proposal: ApplicationSnapshotProposal;
  resume: ApplicationSnapshotResume | null;
  portfolio: ApplicationSnapshotPortfolio[];
}

export interface Application {
  id: string;
  user_id: string;
  job_id: string;
  proposal_id: string | null;
  resume_id: string | null;
  portfolio_ids: string[];
  status: ApplicationStatus;
  applied_at: string | null;
  viewed_at: string | null;
  interview_at: string | null;
  offer_at: string | null;
  won_at: string | null;
  rejected_at: string | null;
  withdrawn_at: string | null;
  completed_at: string | null;
  contract_amount: string | null;
  client_response: string | null;
  rejection_reason: string | null;
  notes: string | null;
  snapshot: ApplicationSnapshot | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface ApplicationListResponse {
  items: Application[];
  total: number;
  limit: number;
  offset: number;
}

export interface ApplicationHistoryEntry {
  id: string;
  application_id: string;
  user_id: string | null;
  from_status: string | null;
  to_status: string;
  note: string | null;
  created_at: string;
}

export interface ApplicationDetailsUpdate {
  contract_amount?: string | null;
  client_response?: string | null;
  rejection_reason?: string | null;
  notes?: string | null;
}

// --- Phase 7: Analytics ---

export interface DashboardOverview {
  total_applications: number;
  active_applications: number;
  interviewed_count: number;
  won_count: number;
  completed_count: number;
  lost_count: number;
  total_revenue: string | null;
  average_contract_amount: string | null;
  average_opportunity_score: number | null;
  average_proposal_quality_score: number | null;
}

export interface FunnelMetrics {
  applied: number;
  viewed: number;
  interview: number;
  offer: number;
  won: number;
  completed: number;
}

export interface OutcomeRates {
  viewed_rate: number | null;
  interview_rate: number | null;
  offer_rate: number | null;
  win_rate: number | null;
  completion_rate: number | null;
}

export interface BucketMetrics {
  label: string;
  applications: number;
  interviews: number;
  wins: number;
  interview_rate: number | null;
  win_rate: number | null;
  average_quality_score: number | null;
  average_contract_amount: string | null;
}

export interface TechnologyPerformance {
  technology: string;
  applications: number;
  interviews: number;
  wins: number;
  win_rate: number | null;
  average_opportunity_score: number | null;
  average_proposal_quality_score: number | null;
}

export interface DomainPerformance {
  domain: string;
  applications: number;
  interviews: number;
  wins: number;
  win_rate: number | null;
  average_contract_amount: string | null;
}

export interface BudgetPerformance {
  bucket: string;
  applications: number;
  interviews: number;
  wins: number;
  win_rate: number | null;
  average_contract_amount: string | null;
}

export interface MonthlyRevenuePoint {
  month: string;
  revenue: string;
  wins: number;
}

export interface RevenueMetrics {
  total_revenue: string;
  completed_revenue: string;
  projected_revenue: string;
  average_won_contract: string | null;
  largest_contract: string | null;
  revenue_by_month: MonthlyRevenuePoint[];
}

export interface TimeToStatusBucket {
  label: string;
  count: number;
  avg_hours: number | null;
  p50_hours: number | null;
  p90_hours: number | null;
}

export interface RecentActivityEntry {
  application_id: string;
  job_title: string | null;
  from_status: string | null;
  to_status: string;
  note: string | null;
  created_at: string;
}

// --- Phase 13: Repository improvement suggestions ---

export interface RepositoryImprovement {
  skill: string;
  suggestion: string;
  job_frequency: number;
  job_frequency_pct: number;
}

export interface RepositoryImprovements {
  repository_id: string;
  owner: string;
  name: string;
  github_url: string;
  improvements: RepositoryImprovement[];
}

export interface RepositoryImprovementsReport {
  repositories: RepositoryImprovements[];
  analyzed_job_count: number;
  repository_count: number;
}

// --- Phase 12: Multi-dimensional job confidence ---

export type InterviewChance = "high" | "medium" | "low";

export interface JobConfidenceReport {
  job_id: string;
  overall_match: number;
  technical_match: number;
  domain_match: number;
  architecture_match: number;
  missing_critical_skills: string[];
  interview_chance: InterviewChance;
  rationale: string[];
}

// --- Phase 19: Portfolio story builder ---

export interface PortfolioStory {
  job_id: string;
  portfolio_id: string;
  portfolio_title: string;
  business_domain: string | null;
  match_score: number;
  opener: string;
  body: string;
  why_this_fit: string;
  relevant_skills: string[];
}

// --- Phase 11: Skill evidence + gap analysis ---

export type EvidenceSource = "portfolio" | "resume" | "repository";

export interface EvidenceItem {
  source_type: EvidenceSource;
  source_id: string;
  source_label: string;
  snippet: string;
}

export type SkillEvidenceStatus = "strong" | "weak" | "missing";

export interface SkillEvidence {
  name: string;
  category: StackCategory | null;
  importance: number | null;
  evidence: EvidenceItem[];
  best_snippet: string | null;
  confidence: number;
  status: SkillEvidenceStatus;
}

export interface EvidenceReport {
  job_id: string;
  skills: SkillEvidence[];
  counts: { strong: number; weak: number; missing: number };
  portfolio_count: number;
  resume_count: number;
  repository_count: number;
}

// --- Phase 8: Scanned GitHub repositories ---

export type RepositoryScanStatus = "pending" | "scanned" | "failed";

export interface StarStory {
  headline: string;
  situation: string;
  task: string;
  action: string;
  result: string;
}

export interface Repository {
  id: string;
  user_id: string;
  github_url: string;
  owner: string;
  name: string;
  default_branch: string | null;
  description: string | null;
  languages: Record<string, number>;
  frameworks: string[];
  libraries: string[];
  databases: string[];
  authentication: string[];
  ai_providers: string[];
  cloud: string[];
  ci_systems: string[];
  test_frameworks: string[];
  has_docker: boolean;
  has_ci: boolean;
  has_tests: boolean;
  architecture_summary: string | null;
  business_domain: string | null;
  strengths: string[];
  highlights: string[];
  readme_excerpt: string | null;
  scan_status: RepositoryScanStatus;
  scan_error: string | null;
  scanned_at: string | null;
  star_story: StarStory | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface RepositoryListResponse {
  items: Repository[];
  total: number;
  limit: number;
  offset: number;
}

export interface RepositoryCreate {
  github_url: string;
  scan_now?: boolean;
}

export interface RepositoryMatch {
  repository_id: string;
  owner: string;
  name: string;
  github_url: string;
  match_score: number;
  semantic_score: number;
  skill_overlap_score: number;
  domain_overlap_score: number;
  architecture_score: number;
  match_reasons: string[];
  matched_skills: string[];
  missing_skills: string[];
  relevant_domains: string[];
  relevant_paths: string[];
  suggested_talking_points: string[];
}

export interface RepositoryMatchesResponse {
  job_id: string;
  matches: RepositoryMatch[];
  embedding_provider: string;
  embedding_model: string;
  repository_count: number;
}

// --- Job import from screenshot ---

export interface JobImportPreview {
  project_duration: string | null;
  project_type: string | null;
  experience_level: string | null;
  location: string | null;
  posted_at: string | null;
  mandatory_skills: string[];
  nice_to_have_skills: string[];
  questions: string[];
}

export interface JobImportResponse {
  job: Job;
  preview: JobImportPreview;
  provider: string;
  model: string;
}

export interface AnalyticsDashboardResponse {
  range: { from_date: string | null; to_date: string | null };
  overview: DashboardOverview;
  funnel: FunnelMetrics;
  outcomes: OutcomeRates;
  score_effectiveness: { buckets: BucketMetrics[] };
  proposal_quality_effectiveness: { buckets: BucketMetrics[] };
  technologies: TechnologyPerformance[];
  domains: DomainPerformance[];
  budgets: BudgetPerformance[];
  revenue: RevenueMetrics;
  time_to_status: { buckets: TimeToStatusBucket[] };
  recent_activity: { items: RecentActivityEntry[] };
}

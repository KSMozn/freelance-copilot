export interface SignupsPoint {
  day: string;
  count: number;
}

export interface WizardFunnel {
  registered: number;
  basics: number;
  education: number;
  photo: number;
  skills: number;
  courses: number;
  projects: number;
  internships: number;
  volunteer: number;
  languages: number;
  certificates: number;
  summary: number;
  preview: number;
  starter_pack: number;
  downloaded: number;
}

export interface AdminEntryDetail {
  id: string;
  kind: string;
  title: string;
  organization: string | null;
  start_date: string | null;
  end_date: string | null;
  is_current: boolean;
  description: string | null;
  url: string | null;
  details: Record<string, unknown>;
  sort_order: number;
  created_at: string;
  updated_at: string;
}

export interface AdminEntriesResponse {
  items: AdminEntryDetail[];
}

export interface EntryKindCount {
  kind: string;
  count: number;
}

export interface UsageKindCount {
  kind: string;
  count: number;
  errors: number;
}

export interface AdminOverview {
  users_total: number;
  users_students: number;
  users_active_7d: number;
  signups_today: number;
  signups_7d: number;
  signups_30d: number;
  signups_series: SignupsPoint[];
  funnel: WizardFunnel;
  entries_by_kind: EntryKindCount[];
  usage_by_kind_7d: UsageKindCount[];
}

export interface AdminUserRow {
  id: string;
  email: string;
  full_name: string | null;
  persona_kind: string;
  is_active: boolean;
  is_superuser: boolean;
  email_verified: boolean;
  last_login_at: string | null;
  created_at: string;
  wizard_step: string | null;
  wizard_completed: number;
  has_linkedin: boolean | null;
  has_github: boolean | null;
  has_downloaded_cv: boolean | null;
}

export interface AdminUserListResponse {
  items: AdminUserRow[];
  total: number;
  page: number;
  size: number;
}

export interface AdminStudentSummary {
  full_name: string | null;
  professional_email: string | null;
  phone: string | null;
  location: string | null;
  date_of_birth: string | null;
  college: string | null;
  department: string | null;
  degree: string | null;
  major: string | null;
  graduation_year: number | null;
  gpa: string | null;
  headline: string | null;
  summary: string | null;
  links: Record<string, unknown>;
  interests: unknown[];
  completed_steps: string[];
  current_step: string | null;
  cv_template_slug: string | null;
  photo_file_id: string | null;
  entries_count: number;
  entries_by_kind: Record<string, number>;
  updated_at: string;
}

export interface AdminUserDetail {
  id: string;
  email: string;
  full_name: string | null;
  persona_kind: string;
  is_active: boolean;
  is_superuser: boolean;
  email_verified_at: string | null;
  last_login_at: string | null;
  created_at: string;
  student: AdminStudentSummary | null;
}

export interface AdminActivityRow {
  id: string;
  user_id: string | null;
  user_email: string | null;
  kind: string;
  status: "ok" | "error";
  duration_ms: number | null;
  error_message: string | null;
  meta: Record<string, unknown>;
  created_at: string;
}

export interface AdminActivityResponse {
  items: AdminActivityRow[];
  total: number;
  page: number;
  size: number;
}

export interface AdminActionResult {
  ok: boolean;
  message: string | null;
}

export interface AdminImpersonateResponse {
  target_user_id: string;
  target_user_email: string;
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface AdminCvTemplate {
  slug: string;
  display_name: string;
  description: string;
  is_visible: boolean;
  sort_order: number;
  created_at: string;
  updated_at: string;
}

export interface AdminCvTemplateListResponse {
  items: AdminCvTemplate[];
}

export interface AdminCvTemplateUpdate {
  is_visible?: boolean;
  sort_order?: number;
}

// ---- Feedback triage ---------------------------------------------------

export type FeedbackKind = "general" | "post_download";

export interface AdminFeedbackItem {
  id: string;
  user_id: string;
  user_email: string | null;
  user_full_name: string | null;
  kind: FeedbackKind;
  rating: number | null;
  message: string | null;
  template_slug: string | null;
  created_at: string;
  resolved_at: string | null;
  resolved_by_email: string | null;
}

export interface AdminFeedbackListResponse {
  items: AdminFeedbackItem[];
  total: number;
  unresolved_count: number;
}

// ---- Admin-triggered emails --------------------------------------------

export interface EmailTemplateSpec {
  id: string;
  name: string;
  description: string;
  subject: string;
  audience_hint: string | null;
}

export interface EmailPreviewResponse {
  subject: string;
  html: string;
  text: string;
  recipient_email: string;
  recipient_name: string | null;
  recent_send_at: string | null;
}

export interface BulkRecipient {
  user_id: string;
  email: string;
  full_name: string | null;
  has_recent_send: boolean;
}

export interface SendEmailBulkDryRunResponse {
  template_id: string;
  recipients: BulkRecipient[];
}

export interface BulkFailure {
  user_id: string;
  error: string;
}

export interface SendEmailBulkResponse {
  template_id: string;
  sent: number;
  skipped: number;
  failed: BulkFailure[];
}

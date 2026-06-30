export type StudentEntryKind =
  | "course"
  | "project"
  | "volunteer"
  | "certificate"
  | "skill"
  | "award"
  | "extracurricular"
  | "language";

export interface StudentLinks {
  github?: string | null;
  linkedin?: string | null;
  website?: string | null;
  portfolio?: string | null;
}

export interface StudentProfile {
  user_id: string;
  full_name: string | null;
  professional_email: string | null;
  phone: string | null;
  location: string | null;
  college: string | null;
  department: string | null;
  degree: string | null;
  major: string | null;
  graduation_year: number | null;
  gpa: string | null;
  photo_file_id: string | null;
  photo_url: string | null;
  summary: string | null;
  headline: string | null;
  links: StudentLinks;
  interests: string[];
  completed_steps: string[];
  current_step: string | null;
  created_at: string;
  updated_at: string;
}

export interface StudentProfileUpdate {
  full_name?: string | null;
  professional_email?: string | null;
  phone?: string | null;
  location?: string | null;
  college?: string | null;
  department?: string | null;
  degree?: string | null;
  major?: string | null;
  graduation_year?: number | null;
  gpa?: string | number | null;
  summary?: string | null;
  headline?: string | null;
  links?: StudentLinks;
  interests?: string[];
  mark_steps?: string[];
  current_step?: string | null;
}

export interface StudentEntry {
  id: string;
  kind: StudentEntryKind;
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

export interface StudentEntryUpsert {
  kind: StudentEntryKind;
  title: string;
  organization?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  is_current?: boolean;
  description?: string | null;
  url?: string | null;
  details?: Record<string, unknown>;
  sort_order?: number;
}

export interface CoachWarning {
  code: string;
  message: string;
  severity: "info" | "warn" | "block";
}

export interface CoachSuggestion {
  label: string;
  value: string;
  rationale?: string | null;
}

export interface EmailCoachResponse {
  ok: boolean;
  warnings: CoachWarning[];
  suggestions: CoachSuggestion[];
}

export interface PhotoCoachResponse {
  ok: boolean;
  warnings: CoachWarning[];
  summary: string | null;
}

export interface TextCoachResponse {
  ok: boolean;
  rewritten: string;
  notes: string[];
}

export interface DraftSummaryResponse {
  ok: boolean;
  headline: string;
  summary: string;
  notes: string[];
}

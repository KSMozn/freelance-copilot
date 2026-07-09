import type {
  InternshipField,
  InternshipWorkMode,
} from "@/features/student-wizard/studentTypes";

export interface InternshipCoachRequest {
  organization: string;
  title: string;
  field?: InternshipField | null;
  location?: string | null;
  work_mode?: InternshipWorkMode | null;
  department?: string | null;
  responsibilities?: string | null;
  achievements?: string | null;
  tools?: string[];
  skills_gained?: string[];
  follow_up_answers?: string[];
}

export interface InternshipCoachResponse {
  ok: boolean;
  vague: boolean;
  summary?: string | null;
  bullets: string[];
  tools_suggested: string[];
  skills_suggested: string[];
  follow_ups: string[];
  notes: string[];
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

export type ProofreadCategory = "typo" | "grammar" | "clarity" | "style";
export type ProofreadField = "summary" | "headline" | "description" | "title";

export interface ProofreadFix {
  entity_kind: "profile" | "entry";
  entity_id: string | null;
  field: ProofreadField;
  original: string;
  suggested: string;
  reason: string;
  category: ProofreadCategory;
}

export interface ProofreadResponse {
  ok: boolean;
  fixes: ProofreadFix[];
  notes: string[];
}

export type FeedbackKind = "general" | "post_download";

export interface FeedbackEntry {
  id: string;
  user_id: string;
  kind: FeedbackKind;
  rating: number | null;
  message: string | null;
  template_slug: string | null;
  created_at: string;
}

export interface GeneralFeedbackCreate {
  message: string;
}

export interface SurveyCreate {
  rating: number;
  comment?: string | null;
  template_slug?: string | null;
}

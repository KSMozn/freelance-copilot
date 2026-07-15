export type FeedbackKind = "general" | "post_download";

export interface FeedbackEntry {
  id: string;
  user_id: string;
  kind: FeedbackKind;
  rating: number | null;
  message: string | null;
  template_slug: string | null;
  screenshot_file_id: string | null;
  created_at: string;
}

export interface GeneralFeedbackCreate {
  message: string;
  screenshot?: File | null;
}

export interface SurveyCreate {
  rating: number;
  comment?: string | null;
  template_slug?: string | null;
}

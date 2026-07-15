import { useMutation } from "@tanstack/react-query";

import { api } from "@/app/apiClient";
import type {
  FeedbackEntry,
  GeneralFeedbackCreate,
  SurveyCreate,
} from "@/features/student-wizard/feedback/feedbackTypes";

export function useSubmitFeedback() {
  return useMutation({
    mutationFn: async ({ message, screenshot }: GeneralFeedbackCreate): Promise<FeedbackEntry> => {
      const form = new FormData();
      form.append("message", message);
      if (screenshot) form.append("screenshot", screenshot);
      const { data } = await api.post<FeedbackEntry>("/students/feedback", form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      return data;
    },
  });
}

export function useSubmitSurvey() {
  return useMutation({
    mutationFn: async (payload: SurveyCreate): Promise<FeedbackEntry> => {
      const { data } = await api.post<FeedbackEntry>("/students/survey", payload);
      return data;
    },
  });
}

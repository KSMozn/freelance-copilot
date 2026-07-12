import { useMutation } from "@tanstack/react-query";

import { api } from "@/app/apiClient";
import type {
  FeedbackEntry,
  GeneralFeedbackCreate,
  SurveyCreate,
} from "@/features/student-wizard/feedback/feedbackTypes";

export function useSubmitFeedback() {
  return useMutation({
    mutationFn: async (payload: GeneralFeedbackCreate): Promise<FeedbackEntry> => {
      const { data } = await api.post<FeedbackEntry>("/students/feedback", payload);
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

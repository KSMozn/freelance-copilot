import { useMutation } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type {
  FeedbackEntry,
  GeneralFeedbackCreate,
  SurveyCreate,
} from "@/types/feedback";

export function useSubmitFeedback() {
  return useMutation({
    mutationFn: async (
      payload: GeneralFeedbackCreate,
    ): Promise<FeedbackEntry> => {
      const { data } = await api.post<FeedbackEntry>(
        "/students/feedback",
        payload,
      );
      return data;
    },
  });
}

export function useSubmitSurvey() {
  return useMutation({
    mutationFn: async (payload: SurveyCreate): Promise<FeedbackEntry> => {
      const { data } = await api.post<FeedbackEntry>(
        "/students/survey",
        payload,
      );
      return data;
    },
  });
}

import { useMutation } from "@tanstack/react-query";

import { api } from "@/app/apiClient";
import type {
  DraftSummaryResponse,
  EmailCoachResponse,
  InternshipCoachRequest,
  InternshipCoachResponse,
  PhotoCoachResponse,
  ProofreadResponse,
  TextCoachResponse,
} from "@/features/student-wizard/coaching/coachingTypes";

export function useCoachEmail() {
  return useMutation({
    mutationFn: async (payload: {
      email: string;
      full_name?: string | null;
    }): Promise<EmailCoachResponse> => {
      const { data } = await api.post<EmailCoachResponse>(
        "/students/coach/email",
        payload,
      );
      return data;
    },
  });
}

export function useCoachPhoto() {
  return useMutation({
    mutationFn: async (file: File): Promise<PhotoCoachResponse> => {
      const form = new FormData();
      form.append("file", file);
      const { data } = await api.post<PhotoCoachResponse>(
        "/students/coach/photo",
        form,
        { headers: { "Content-Type": "multipart/form-data" } },
      );
      return data;
    },
  });
}

export function useProofread() {
  return useMutation({
    mutationFn: async (): Promise<ProofreadResponse> => {
      const { data } = await api.get<ProofreadResponse>(
        "/students/coach/proofread",
      );
      return data;
    },
  });
}

export function useDraftSummary() {
  return useMutation({
    mutationFn: async (): Promise<DraftSummaryResponse> => {
      const { data } = await api.get<DraftSummaryResponse>(
        "/students/coach/draft-summary",
      );
      return data;
    },
  });
}

export function useCoachText() {
  return useMutation({
    mutationFn: async (payload: {
      field:
        | "summary"
        | "project_description"
        | "volunteer_description"
        | "internship_description";
      text: string;
      context?: Record<string, unknown>;
    }): Promise<TextCoachResponse> => {
      const { data } = await api.post<TextCoachResponse>(
        "/students/coach/text",
        payload,
      );
      return data;
    },
  });
}

export function useImproveInternship() {
  return useMutation({
    mutationFn: async (
      payload: InternshipCoachRequest,
    ): Promise<InternshipCoachResponse> => {
      const { data } = await api.post<InternshipCoachResponse>(
        "/students/coach/internship",
        payload,
      );
      return data;
    },
  });
}

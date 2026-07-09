import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/app/apiClient";
import type {
  CareerPack,
  GitHubGenerated,
  GitHubReview,
  LinkedInGenerated,
  LinkedInReview,
} from "@/features/student-wizard/career-pack/careerPackTypes";

const CAREER_PACK_KEY = ["student", "career-pack"] as const;

export function useCareerPack() {
  return useQuery({
    queryKey: CAREER_PACK_KEY,
    queryFn: async () => {
      const { data } = await api.get<CareerPack>("/students/career-pack");
      return data;
    },
  });
}

export function useGenerateLinkedIn() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (): Promise<LinkedInGenerated> => {
      const { data } = await api.post<LinkedInGenerated>(
        "/students/career-pack/linkedin/generate",
      );
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: CAREER_PACK_KEY }),
  });
}

export function useReviewLinkedIn() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: {
      linkedinUrl: string;
      file: File;
    }): Promise<LinkedInReview> => {
      const form = new FormData();
      form.append("linkedin_url", payload.linkedinUrl);
      form.append("file", payload.file);
      const { data } = await api.post<LinkedInReview>(
        "/students/career-pack/linkedin/review",
        form,
        { headers: { "Content-Type": "multipart/form-data" } },
      );
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: CAREER_PACK_KEY }),
  });
}

export function useGenerateGitHub() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (): Promise<GitHubGenerated> => {
      const { data } = await api.post<GitHubGenerated>(
        "/students/career-pack/github/generate",
      );
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: CAREER_PACK_KEY }),
  });
}

export function useReviewGitHub() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (identifier: string): Promise<GitHubReview> => {
      const { data } = await api.post<GitHubReview>(
        "/students/career-pack/github/review",
        { identifier },
      );
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: CAREER_PACK_KEY }),
  });
}

export function useClearCareerPack() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: {
      side: "linkedin" | "github";
      kind: "generated" | "recommendations";
    }): Promise<CareerPack> => {
      const { data } = await api.post<CareerPack>(
        "/students/career-pack/clear",
        payload,
      );
      return data;
    },
    onSuccess: (data) => qc.setQueryData(CAREER_PACK_KEY, data),
  });
}
